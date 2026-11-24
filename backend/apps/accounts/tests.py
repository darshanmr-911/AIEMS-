from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.academics.models import Department, Semester


class RoleSecurityTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        User.objects.create_user(
            username='hod-test', password='StrongPass123!', role=User.Role.HOD
        )
        self.department = Department.objects.create(name='Computer Science', code='CSE')
        self.semester = Semester.objects.create(
            semester_number=1, department=self.department, academic_year='2025-2026'
        )

    def login(self, username, password):
        return self.client.post('/api/auth/login/', {
            'username': username, 'password': password
        }, format='json')

    def test_hod_login_and_dashboard(self):
        login = self.login('hod-test', 'StrongPass123!')
        self.assertEqual(login.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = self.client.get('/api/hod/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_student_registration(self):
        response = self.client.post('/api/auth/register/student/', {
            'username': 'student-test',
            'first_name': 'Test',
            'last_name': 'Student',
            'email': 'student@example.edu',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
            'usn': 'AIEMS001',
            'department': self.department.id,
            'semester': self.semester.id,
            'academic_year': '2025-2026',
        }, format='json')
        self.assertEqual(response.status_code, 201)

    def test_student_cannot_create_teacher(self):
        User = get_user_model()
        User.objects.create_user(
            username='student', password='StrongPass123!', role=User.Role.STUDENT
        )
        login = self.login('student', 'StrongPass123!')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = self.client.post('/api/hod/teachers/', {
            'username': 'unauthorized',
            'password': 'StrongPass123!',
            'employee_id': 'EMP001',
            'department': self.department.id,
        }, format='json')
        self.assertIn(response.status_code, (401, 403))
