from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower


class User(AbstractUser):
    class Role(models.TextChoices):
        HOD = 'HOD', 'HOD'
        TEACHER = 'TEACHER', 'Teacher'
        STUDENT = 'STUDENT', 'Student'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    department = models.ForeignKey(
        'academics.Department',
        on_delete=models.PROTECT,
        related_name='members',
        null=True,
        blank=True,
    )
    must_change_password = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('email'),
                condition=Q(role__in=['HOD', 'TEACHER']) & ~Q(email=''),
                name='unique_staff_email_ci',
            ),
        ]

    def is_hod(self):
        return self.role == self.Role.HOD

    def is_teacher(self):
        return self.role == self.Role.TEACHER

    def is_student(self):
        return self.role == self.Role.STUDENT


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    usn = models.CharField(max_length=30, unique=True)
    department = models.ForeignKey('academics.Department', on_delete=models.PROTECT, related_name='students')
    semester = models.ForeignKey('academics.Semester', on_delete=models.PROTECT, related_name='students')
    academic_year = models.CharField(max_length=9)

    def __str__(self):
        return f'{self.user.get_full_name()} ({self.usn})'


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=30, unique=True)
    department = models.ForeignKey('academics.Department', on_delete=models.PROTECT, related_name='teachers')
    designation = models.CharField(max_length=100, default='Teacher')

    def __str__(self):
        return f'{self.user.get_full_name()} ({self.employee_id})'


class AuditLog(models.Model):
    department = models.ForeignKey(
        'academics.Department',
        on_delete=models.PROTECT,
        related_name='audit_events',
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='audit_events',
    )
    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='targeted_audit_events',
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=64)
    target_type = models.CharField(max_length=64, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['department', 'created_at'])]
