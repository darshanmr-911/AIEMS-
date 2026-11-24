from django.db import models


class TeacherSubjectAssignment(models.Model):
    teacher = models.ForeignKey(
        'accounts.TeacherProfile', on_delete=models.CASCADE, related_name='subject_assignments'
    )
    subject = models.ForeignKey(
        'academics.Subject', on_delete=models.CASCADE, related_name='teacher_assignments'
    )
    academic_year = models.CharField(max_length=9)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['teacher', 'subject', 'academic_year'],
                name='unique_teacher_subject_year',
            )
        ]

# Create your models here.
