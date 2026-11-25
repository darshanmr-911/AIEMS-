from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from apps.academics.models import Department, Semester, Subject
from apps.accounts.models import TeacherProfile
from apps.materials.models import StudyMaterial
from apps.teachers.models import TeacherSubjectAssignment

User = get_user_model()


class PublicMaterialAccessTests(APITestCase):
    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

        self.aiml = Department.objects.create(name='Artificial Intelligence', code='AIML')
        self.cse = Department.objects.create(name='Computer Science', code='CSE')
        self.aiml_semester = Semester.objects.create(
            semester_number=1,
            department=self.aiml,
            academic_year='2025-2026',
        )
        self.cse_semester = Semester.objects.create(
            semester_number=1,
            department=self.cse,
            academic_year='2025-2026',
        )
        self.aiml_subject = Subject.objects.create(
            subject_name='Machine Learning',
            subject_code='AIML101',
            department=self.aiml,
            semester=self.aiml_semester,
        )
        self.cse_subject = Subject.objects.create(
            subject_name='Data Structures',
            subject_code='CSE101',
            department=self.cse,
            semester=self.cse_semester,
        )
        self.approved = self.create_material(
            'Approved AIML notes',
            self.aiml,
            self.aiml_semester,
            self.aiml_subject,
            StudyMaterial.Status.APPROVED,
        )
        self.pending = self.create_material(
            'Pending AIML notes',
            self.aiml,
            self.aiml_semester,
            self.aiml_subject,
            StudyMaterial.Status.PENDING,
        )
        self.other_department = self.create_material(
            'Approved CSE notes',
            self.cse,
            self.cse_semester,
            self.cse_subject,
            StudyMaterial.Status.APPROVED,
        )

    def create_material(self, title, department, semester, subject, approval_status):
        return StudyMaterial.objects.create(
            title=title,
            department=department,
            semester=semester,
            subject=subject,
            material_type=StudyMaterial.MaterialType.NOTES,
            file=SimpleUploadedFile(
                f'{title.lower().replace(" ", "-")}.pdf',
                b'%PDF-1.4 test content',
                content_type='application/pdf',
            ),
            academic_year=semester.academic_year,
            approval_status=approval_status,
        )

    def test_public_library_only_lists_approved_materials_and_filters_department(self):
        response = self.client.get('/api/public/materials/', {'department__code': 'AIML'})
        self.assertEqual(response.status_code, 200)
        results = response.data['results'] if isinstance(response.data, dict) else response.data
        self.assertEqual([material['id'] for material in results], [self.approved.id])
        self.assertEqual(results[0]['department_code'], 'AIML')

    def test_public_download_is_available_only_for_approved_materials(self):
        response = self.client.get(f'/api/public/materials/{self.approved.id}/download/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'%PDF-1.4 test content')

        pending = self.client.get(f'/api/public/materials/{self.pending.id}/download/')
        self.assertEqual(pending.status_code, 404)

    def test_public_filters_combine_department_year_semester_subject_and_type(self):
        response = self.client.get('/api/public/materials/', {
            'department_code': 'AIML',
            'study_year': 1,
            'semester': 1,
            'subject': self.aiml_subject.id,
            'material_type': StudyMaterial.MaterialType.NOTES,
            'search': 'Approved',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data['results']], [self.approved.id])

        no_match = self.client.get('/api/public/materials/', {
            'department_code': 'AIML',
            'study_year': 4,
        })
        self.assertEqual(no_match.status_code, 200)
        self.assertEqual(no_match.data['results'], [])

    def test_public_subject_options_follow_the_selected_filters(self):
        response = self.client.get('/api/public/materials/options/', {
            'department_code': 'AIML',
            'study_year': 1,
            'semester': 1,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [{
            'id': self.aiml_subject.id,
            'name': self.aiml_subject.subject_name,
            'code': self.aiml_subject.subject_code,
        }])


class HodMaterialWorkflowTests(APITestCase):
    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

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
        self.other_semester = Semester.objects.create(
            semester_number=1,
            department=self.cse,
            academic_year='2025-2026',
        )
        self.other_subject = Subject.objects.create(
            subject_name='Data Structures',
            subject_code='CSE101',
            department=self.cse,
            semester=self.other_semester,
        )
        self.hod = User.objects.create_user(
            username='hod-aiml',
            email='hodaiml@aiems.edu.in',
            password='StrongPass123!',
            role=User.Role.HOD,
            department=self.aiml,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {AccessToken.for_user(self.hod)}')

    def upload_data(self, subject_id, semester_id):
        return {
            'title': 'AIML department upload',
            'description': 'Study resource',
            'semester': semester_id,
            'subject': subject_id,
            'material_type': 'NOTES',
            'academic_year': '2025-2026',
            'file': SimpleUploadedFile('notes.pdf', b'%PDF-1.4 content', content_type='application/pdf'),
        }

    def test_hod_upload_is_department_bound_and_approved(self):
        response = self.client.post(
            '/api/hod/materials/',
            self.upload_data(self.subject.id, self.semester.id),
            format='multipart',
        )
        self.assertEqual(response.status_code, 201, response.data)
        material = StudyMaterial.objects.get(pk=response.data['id'])
        self.assertEqual(material.department_id, self.aiml.id)
        self.assertEqual(material.created_by_id, self.hod.id)
        self.assertEqual(material.approval_status, StudyMaterial.Status.APPROVED)

    def test_hod_cannot_upload_material_for_another_department(self):
        response = self.client.post(
            '/api/hod/materials/',
            self.upload_data(self.other_subject.id, self.other_semester.id),
            format='multipart',
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(StudyMaterial.objects.exists())

    def test_hod_cannot_view_or_delete_another_department_material(self):
        material = StudyMaterial.objects.create(
            title='CSE private material',
            department=self.cse,
            semester=self.other_semester,
            subject=self.other_subject,
            material_type=StudyMaterial.MaterialType.NOTES,
            file=SimpleUploadedFile('cse.pdf', b'%PDF-1.4 cse', content_type='application/pdf'),
            academic_year=self.other_semester.academic_year,
        )
        self.assertEqual(self.client.get(f'/api/hod/materials/{material.id}/').status_code, 404)
        self.assertEqual(self.client.delete(f'/api/hod/materials/{material.id}/').status_code, 404)

    def test_teacher_upload_history_is_visible_only_inside_hod_department(self):
        teacher = User.objects.create_user(
            username='aiml-teacher',
            email='aiml.teacher@aiems.edu.in',
            password='TeacherPass123!',
            role=User.Role.TEACHER,
            department=self.aiml,
        )
        profile = TeacherProfile.objects.create(
            user=teacher,
            employee_id='EMP-AIML-01',
            department=self.aiml,
        )
        upload = StudyMaterial.objects.create(
            title='Teacher notes',
            uploaded_by=profile,
            department=self.aiml,
            semester=self.semester,
            subject=self.subject,
            material_type=StudyMaterial.MaterialType.NOTES,
            file=SimpleUploadedFile('teacher-notes.pdf', b'%PDF-1.4 content', content_type='application/pdf'),
            academic_year='2025-2026',
            approval_status=StudyMaterial.Status.PENDING,
        )
        visible = self.client.get(f'/api/hod/teachers/{teacher.id}/uploads/')
        self.assertEqual(visible.status_code, 200)
        self.assertEqual([item['id'] for item in visible.data], [upload.id])

        other_teacher = User.objects.create_user(
            username='cse-teacher',
            email='cse.teacher@aiems.edu.in',
            password='TeacherPass123!',
            role=User.Role.TEACHER,
            department=self.cse,
        )
        TeacherProfile.objects.create(
            user=other_teacher,
            employee_id='EMP-CSE-01',
            department=self.cse,
        )
        hidden = self.client.get(f'/api/hod/teachers/{other_teacher.id}/uploads/')
        self.assertEqual(hidden.status_code, 404)


class TeacherMaterialWorkflowTests(APITestCase):
    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

        self.department = Department.objects.create(name='Artificial Intelligence', code='AIML')
        self.other_department = Department.objects.create(name='Computer Science', code='CSE')
        self.semester = Semester.objects.create(
            semester_number=1,
            department=self.department,
            academic_year='2025-2026',
        )
        self.subject = Subject.objects.create(
            subject_name='Machine Learning',
            subject_code='AIML101',
            department=self.department,
            semester=self.semester,
        )
        self.other_semester = Semester.objects.create(
            semester_number=1,
            department=self.other_department,
            academic_year='2025-2026',
        )
        self.other_subject = Subject.objects.create(
            subject_name='Data Structures',
            subject_code='CSE101',
            department=self.other_department,
            semester=self.other_semester,
        )
        self.teacher = User.objects.create_user(
            username='aiml.teacher@aiems.edu.in',
            email='aiml.teacher@aiems.edu.in',
            password='TeacherPass123!',
            role=User.Role.TEACHER,
            department=self.department,
        )
        self.profile = TeacherProfile.objects.create(
            user=self.teacher,
            employee_id='EMP-AIML-01',
            department=self.department,
        )
        TeacherSubjectAssignment.objects.create(
            teacher=self.profile,
            subject=self.subject,
            academic_year=self.semester.academic_year,
        )

    def login_teacher(self):
        return self.client.post('/api/auth/teacher/login/', {
            'email': self.teacher.email,
            'password': 'TeacherPass123!',
        }, format='json')

    def authenticate(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {AccessToken.for_user(user)}')

    def upload_data(self, **overrides):
        payload = {
            'title': 'Teacher study notes',
            'description': 'Notes for the current semester',
            'semester': self.semester.id,
            'subject': self.subject.id,
            'material_type': StudyMaterial.MaterialType.NOTES,
            'academic_year': self.semester.academic_year,
            'department': self.other_department.id,
            'file': SimpleUploadedFile(
                'teacher-notes.pdf',
                b'%PDF-1.4 teacher content',
                content_type='application/pdf',
            ),
        }
        payload.update(overrides)
        return payload

    def test_teacher_login_forces_password_change_before_material_access(self):
        self.teacher.must_change_password = True
        self.teacher.save(update_fields=['must_change_password'])
        login = self.login_teacher()
        self.assertEqual(login.status_code, 200, login.data)
        self.assertTrue(login.data['must_change_password'])
        self.assertEqual(login.data['user']['department']['code'], 'AIML')
        self.assertNotIn('password', login.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        self.assertEqual(self.client.get('/api/teacher/materials/').status_code, 403)

        changed = self.client.post('/api/auth/password/change/', {
            'current_password': 'TeacherPass123!',
            'new_password': 'TeacherChanged456!',
            'password_confirm': 'TeacherChanged456!',
        }, format='json')
        self.assertEqual(changed.status_code, 200, changed.data)
        self.assertFalse(changed.data['must_change_password'])
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {changed.data['access']}")
        self.assertEqual(self.client.get('/api/teacher/materials/').status_code, 200)

    def test_teacher_can_upload_edit_and_archive_only_own_materials(self):
        self.authenticate(self.teacher)
        upload = self.client.post(
            '/api/teacher/materials/',
            self.upload_data(),
            format='multipart',
        )
        self.assertEqual(upload.status_code, 201, upload.data)
        material = StudyMaterial.objects.get(pk=upload.data['id'])
        self.assertEqual(material.department_id, self.department.id)
        self.assertEqual(material.uploaded_by_id, self.profile.id)
        self.assertEqual(material.approval_status, StudyMaterial.Status.PENDING)

        edited = self.client.patch(
            f'/api/teacher/materials/{material.id}/',
            {'title': 'Revised teacher notes'},
            format='json',
        )
        self.assertEqual(edited.status_code, 200, edited.data)
        material.refresh_from_db()
        self.assertEqual(material.title, 'Revised teacher notes')
        self.assertEqual(material.approval_status, StudyMaterial.Status.PENDING)

        deleted = self.client.delete(f'/api/teacher/materials/{material.id}/')
        self.assertEqual(deleted.status_code, 204)
        material.refresh_from_db()
        self.assertEqual(material.approval_status, StudyMaterial.Status.ARCHIVED)

    def test_teacher_cannot_upload_unassigned_or_other_department_subjects(self):
        self.authenticate(self.teacher)
        response = self.client.post(
            '/api/teacher/materials/',
            self.upload_data(subject=self.other_subject.id, semester=self.other_semester.id),
            format='multipart',
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(StudyMaterial.objects.exists())

    def test_teacher_cannot_view_or_delete_another_teachers_material(self):
        other_teacher = User.objects.create_user(
            username='other.teacher@aiems.edu.in',
            email='other.teacher@aiems.edu.in',
            password='TeacherPass123!',
            role=User.Role.TEACHER,
            department=self.department,
        )
        other_profile = TeacherProfile.objects.create(
            user=other_teacher,
            employee_id='EMP-AIML-02',
            department=self.department,
        )
        material = StudyMaterial.objects.create(
            title='Other teacher upload',
            uploaded_by=other_profile,
            department=self.department,
            semester=self.semester,
            subject=self.subject,
            material_type=StudyMaterial.MaterialType.NOTES,
            file=SimpleUploadedFile('other.pdf', b'%PDF-1.4 other', content_type='application/pdf'),
            academic_year=self.semester.academic_year,
        )
        self.authenticate(self.teacher)
        self.assertEqual(self.client.get('/api/teacher/materials/').data['results'], [])
        self.assertEqual(self.client.get(f'/api/teacher/materials/{material.id}/').status_code, 404)
        self.assertEqual(self.client.delete(f'/api/teacher/materials/{material.id}/').status_code, 404)

    def test_teacher_material_endpoints_require_authentication(self):
        response = self.client.get('/api/teacher/materials/')
        self.assertIn(response.status_code, (401, 403))
