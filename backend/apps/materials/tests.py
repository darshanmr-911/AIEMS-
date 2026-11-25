from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from apps.academics.models import Department, Semester, Subject
from apps.accounts.models import TeacherProfile
from apps.materials.models import StudyMaterial

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
            category=StudyMaterial.Category.NOTES,
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
            'category': 'NOTES',
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
            category=StudyMaterial.Category.NOTES,
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
