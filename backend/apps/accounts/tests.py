import os
import re
from io import StringIO
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from apps.academics.defaults import DEFAULT_DEPARTMENTS
from apps.academics.models import Department, Semester, Subject
from apps.accounts.models import TeacherProfile
from apps.teachers.models import TeacherSubjectAssignment

User = get_user_model()


class DepartmentHodAccessTests(APITestCase):
    def setUp(self):
        self.aiml = Department.objects.create(name='Artificial Intelligence', code='AIML')
        self.cse = Department.objects.create(name='Computer Science', code='CSE')
        self.semester = Semester.objects.create(
            semester_number=1,
            department=self.aiml,
            academic_year='2025-2026',
        )
        self.subject = Subject.objects.create(
            subject_name='Machine Learning',
            subject_code='AIML101',
            department=self.aiml,
            semester=self.semester,
        )
        self.hod = User.objects.create_user(
            username='hod-aiml',
            email='hodaiml@aiems.edu.in',
            password='StrongPass123!',
            role=User.Role.HOD,
            department=self.aiml,
        )
        self.other_hod = User.objects.create_user(
            username='hod-cse',
            email='hodcse@aiems.edu.in',
            password='StrongPass123!',
            role=User.Role.HOD,
            department=self.cse,
        )

    def login_hod(self, email='hodaiml@aiems.edu.in', password='StrongPass123!'):
        return self.client.post(
            '/api/auth/login/',
            {'email': email, 'password': password},
            format='json',
        )

    def authenticate(self, user):
        from rest_framework_simplejwt.tokens import AccessToken

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {AccessToken.for_user(user)}')

    def teacher_payload(self, **overrides):
        payload = {
            'first_name': 'Taylor',
            'last_name': 'Teacher',
            'email': 'taylor.teacher@aiems.edu.in',
            'employee_id': 'EMP-AIML-01',
            'designation': 'Assistant Professor',
            'password': 'TeacherPass123!',
            'password_confirm': 'TeacherPass123!',
        }
        payload.update(overrides)
        return payload

    def test_hod_login_uses_official_email_and_is_department_bound(self):
        response = self.login_hod()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['department']['code'], 'AIML')
        self.assertEqual(response.data['user']['role'], User.Role.HOD)
        self.assertNotIn('password', response.data)

        self.authenticate(self.hod)
        dashboard = self.client.get('/api/hod/dashboard/')
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.data['department']['code'], 'AIML')

    def test_initial_password_requires_change_before_dashboard_access(self):
        self.hod.must_change_password = True
        self.hod.save(update_fields=['must_change_password'])
        login = self.login_hod()
        self.assertEqual(login.status_code, 200)
        self.assertTrue(login.data['must_change_password'])
        self.authenticate(self.hod)

        blocked = self.client.get('/api/hod/dashboard/')
        self.assertEqual(blocked.status_code, 403)
        changed = self.client.post('/api/auth/password/change/', {
            'current_password': 'StrongPass123!',
            'new_password': 'DifferentPass456!',
            'password_confirm': 'DifferentPass456!',
        }, format='json')
        self.assertEqual(changed.status_code, 200)
        self.assertFalse(changed.data['must_change_password'])
        self.assertTrue(self.hod.__class__.objects.get(pk=self.hod.pk).check_password('DifferentPass456!'))

    def test_hod_can_create_and_deactivate_own_department_teacher(self):
        self.authenticate(self.hod)
        created = self.client.post('/api/hod/teachers/', self.teacher_payload(), format='json')
        self.assertEqual(created.status_code, 201, created.data)
        teacher = User.objects.get(email='taylor.teacher@aiems.edu.in')
        profile = TeacherProfile.objects.get(user=teacher)
        self.assertEqual(teacher.department_id, self.aiml.id)
        self.assertEqual(profile.department_id, self.aiml.id)
        self.assertTrue(teacher.must_change_password)
        self.assertNotIn('password', created.data)

        response = self.client.patch(
            f'/api/hod/teachers/{teacher.id}/status/',
            {'is_active': False},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        teacher.refresh_from_db()
        self.assertFalse(teacher.is_active)
        self.assertTrue(TeacherProfile.objects.filter(pk=profile.pk).exists())

    def test_hod_cannot_create_or_view_other_department_teacher(self):
        other_teacher = User.objects.create_user(
            username='other-teacher',
            email='other.teacher@aiems.edu.in',
            password='TeacherPass123!',
            role=User.Role.TEACHER,
            department=self.cse,
        )
        TeacherProfile.objects.create(
            user=other_teacher,
            employee_id='EMP-CSE-01',
            department=self.cse,
        )
        self.authenticate(self.hod)
        response = self.client.post('/api/hod/teachers/', self.teacher_payload(
            email='cross.department@aiems.edu.in',
            employee_id='EMP-CROSS-01',
            department=self.cse.id,
        ), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        created = User.objects.get(email='cross.department@aiems.edu.in')
        self.assertEqual(created.department_id, self.aiml.id)
        self.assertEqual(created.teacher_profile.department_id, self.aiml.id)

        hidden = self.client.get(f'/api/hod/teachers/{other_teacher.id}/')
        self.assertEqual(hidden.status_code, 404)

    def test_hod_cannot_assign_other_department_teacher(self):
        other_teacher = User.objects.create_user(
            username='other-teacher',
            email='other.teacher@aiems.edu.in',
            password='TeacherPass123!',
            role=User.Role.TEACHER,
            department=self.cse,
        )
        profile = TeacherProfile.objects.create(
            user=other_teacher,
            employee_id='EMP-CSE-01',
            department=self.cse,
        )
        self.authenticate(self.hod)
        response = self.client.post('/api/hod/assignments/', {
            'teacher': profile.id,
            'subject': self.subject.id,
            'academic_year': '2025-2026',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(TeacherSubjectAssignment.objects.exists())

    def test_duplicate_staff_email_is_rejected_case_insensitively(self):
        self.authenticate(self.hod)
        first = self.client.post('/api/hod/teachers/', self.teacher_payload(), format='json')
        self.assertEqual(first.status_code, 201, first.data)
        duplicate = self.client.post('/api/hod/teachers/', self.teacher_payload(
            email='TAYLOR.TEACHER@AIEMS.EDU.IN',
            employee_id='EMP-AIML-02',
        ), format='json')
        self.assertEqual(duplicate.status_code, 400)

    def test_teacher_cannot_access_hod_management_apis(self):
        teacher = User.objects.create_user(
            username='aiml-teacher',
            email='aiml.teacher@aiems.edu.in',
            password='TeacherPass123!',
            role=User.Role.TEACHER,
            department=self.aiml,
        )
        response = self.client.post('/api/auth/login/', {
            'email': teacher.email,
            'password': 'TeacherPass123!',
        }, format='json')
        self.assertNotEqual(response.status_code, 200)
        self.authenticate(teacher)
        self.assertEqual(self.client.get('/api/hod/teachers/').status_code, 403)
        self.assertEqual(self.client.get('/api/teacher/materials/').status_code, 403)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_email_and_confirmation(self):
        request = self.client.post('/api/auth/password/reset/', {
            'email': self.hod.email,
        }, format='json')
        self.assertEqual(request.status_code, 202)
        self.assertEqual(len(mail.outbox), 1)

        reset_url = re.search(r'https?://\S+', mail.outbox[0].body).group(0)
        query = parse_qs(urlparse(reset_url).query)
        confirm = self.client.post('/api/auth/password/reset/confirm/', {
            'uid': query['uid'][0],
            'token': query['token'][0],
            'new_password': 'ResetPassword456!',
            'password_confirm': 'ResetPassword456!',
        }, format='json')
        self.assertEqual(confirm.status_code, 200, confirm.data)
        self.hod.refresh_from_db()
        self.assertTrue(self.hod.check_password('ResetPassword456!'))


class InitializeDepartmentHodsTests(TestCase):
    def test_command_is_idempotent_and_does_not_overwrite_existing_passwords(self):
        passwords = {
            f'INITIAL_HOD_PASSWORD_{email_prefix.upper()}': f'Z9!{email_prefix}Qx_26#'
            for _, _, email_prefix in DEFAULT_DEPARTMENTS
        }
        output = StringIO()
        with patch.dict(os.environ, passwords):
            call_command('initialize_department_hods', stdout=output)
            self.assertIn('hodaiml@aiems.edu.in', output.getvalue())
            for password in passwords.values():
                self.assertNotIn(password, output.getvalue())

            user = User.objects.get(email='hodaiml@aiems.edu.in')
            self.assertTrue(user.must_change_password)
            for _, _, email_prefix in DEFAULT_DEPARTMENTS:
                account = User.objects.get(email=f'hod{email_prefix}@aiems.edu.in')
                self.assertTrue(account.must_change_password)
                self.assertTrue(
                    account.check_password(passwords[f'INITIAL_HOD_PASSWORD_{email_prefix.upper()}'])
                )
            user.set_password('ManuallyChangedPassword789!')
            user.must_change_password = False
            user.save(update_fields=['password', 'must_change_password'])

            call_command('initialize_department_hods', stdout=StringIO())
            user.refresh_from_db()
            self.assertTrue(user.check_password('ManuallyChangedPassword789!'))
            self.assertFalse(user.must_change_password)
            self.assertEqual(User.objects.filter(role=User.Role.HOD).count(), 7)

    def test_command_requires_department_password_variables(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(CommandError):
                call_command('initialize_department_hods', stdout=StringIO())
        self.assertFalse(Department.objects.exists())
