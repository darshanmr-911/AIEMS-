from rest_framework import serializers
from .models import StudyMaterial


class StudyMaterialSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.subject_name', read_only=True)
    subject_code = serializers.CharField(source='subject.subject_code', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.user.get_full_name', read_only=True)

    class Meta:
        model = StudyMaterial
        fields = [
            'id', 'title', 'description', 'department', 'semester', 'subject', 'module',
            'category', 'file', 'thumbnail', 'academic_year', 'approval_status',
            'rejection_reason', 'download_count', 'uploaded_at', 'updated_at',
            'subject_name', 'subject_code', 'uploaded_by_name',
        ]
        read_only_fields = [
            'approval_status', 'rejection_reason', 'download_count', 'uploaded_at', 'updated_at',
        ]
