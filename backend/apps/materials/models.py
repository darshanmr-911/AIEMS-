import os
from django.core.exceptions import ValidationError
from django.db import models


def validate_material_file(file):
    allowed = {'.pdf': 'application/pdf', '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'}
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed:
        raise ValidationError('Only PDF, DOCX, and PPTX files are allowed.')
    content_type = getattr(file, 'content_type', '')
    if content_type and content_type not in allowed.values():
        raise ValidationError('The uploaded file type does not match a permitted document format.')
    if file.size > 25 * 1024 * 1024:
        raise ValidationError('File must not exceed 25 MB.')


class StudyMaterial(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        ARCHIVED = 'ARCHIVED', 'Archived'

    class Category(models.TextChoices):
        NOTES = 'NOTES', 'Subject notes'
        PREVIOUS_PAPER = 'PREVIOUS_PAPER', 'Previous year question paper'
        MODEL_PAPER = 'MODEL_PAPER', 'Model question paper'
        INTERNAL_PAPER = 'INTERNAL_PAPER', 'Internal assessment paper'
        ASSIGNMENT = 'ASSIGNMENT', 'Assignment'
        LAB_MANUAL = 'LAB_MANUAL', 'Lab manual'
        PRACTICAL = 'PRACTICAL', 'Practical record'
        SYLLABUS = 'SYLLABUS', 'Syllabus'
        IMPORTANT_QUESTIONS = 'IMPORTANT_QUESTIONS', 'Important questions'
        REFERENCE = 'REFERENCE', 'Reference material'

    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey('accounts.TeacherProfile', on_delete=models.PROTECT, related_name='uploads')
    department = models.ForeignKey('academics.Department', on_delete=models.PROTECT, related_name='materials')
    semester = models.ForeignKey('academics.Semester', on_delete=models.PROTECT, related_name='materials')
    subject = models.ForeignKey('academics.Subject', on_delete=models.PROTECT, related_name='materials')
    module = models.ForeignKey('academics.Module', on_delete=models.PROTECT, null=True, blank=True, related_name='materials')
    category = models.CharField(max_length=30, choices=Category.choices)
    file = models.FileField(upload_to='materials/%Y/%m/', validators=[validate_material_file])
    thumbnail = models.FileField(upload_to='thumbnails/%Y/%m/', blank=True)
    academic_year = models.CharField(max_length=9)
    approval_status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.TextField(blank=True)
    download_count = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['approval_status']),
            models.Index(fields=['academic_year']),
            models.Index(fields=['category']),
        ]


class MaterialApproval(models.Model):
    material = models.OneToOneField(StudyMaterial, on_delete=models.CASCADE, related_name='approval')
    reviewed_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='material_reviews')
    status = models.CharField(max_length=10, choices=StudyMaterial.Status.choices)
    rejection_reason = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(auto_now=True)

# Create your models here.
