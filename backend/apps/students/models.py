from django.db import models


class Bookmark(models.Model):
    student = models.ForeignKey(
        'accounts.StudentProfile', on_delete=models.CASCADE, related_name='bookmarks'
    )
    material = models.ForeignKey(
        'materials.StudyMaterial', on_delete=models.CASCADE, related_name='bookmarks'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'material'], name='unique_student_material_bookmark')
        ]


class DownloadHistory(models.Model):
    student = models.ForeignKey(
        'accounts.StudentProfile', on_delete=models.CASCADE, related_name='downloads'
    )
    material = models.ForeignKey(
        'materials.StudyMaterial', on_delete=models.CASCADE, related_name='download_history'
    )
    downloaded_at = models.DateTimeField(auto_now_add=True)

# Create your models here.
