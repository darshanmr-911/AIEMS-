from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    email_prefix = models.CharField(max_length=16, blank=True, default='')
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Semester(models.Model):
    semester_number = models.PositiveSmallIntegerField()
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='semesters')
    academic_year = models.CharField(max_length=9)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['semester_number', 'department', 'academic_year'],
                name='unique_department_semester_year',
            )
        ]

    def __str__(self):
        return f'Semester {self.semester_number}'


class Subject(models.Model):
    subject_name = models.CharField(max_length=200)
    subject_code = models.CharField(max_length=30)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='subjects')
    semester = models.ForeignKey(Semester, on_delete=models.PROTECT, related_name='subjects')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subject_code', 'department', 'semester'],
                name='unique_subject_code_scope',
            )
        ]
        indexes = [models.Index(fields=['subject_name']), models.Index(fields=['subject_code'])]

    def __str__(self):
        return f'{self.subject_name} ({self.subject_code})'


class Module(models.Model):
    module_number = models.PositiveSmallIntegerField()
    module_name = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='modules')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['module_number', 'subject'], name='unique_module_number_subject')
        ]

    def __str__(self):
        return f'Module {self.module_number}: {self.module_name}'

# Create your models here.
