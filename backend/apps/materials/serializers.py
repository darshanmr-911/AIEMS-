from rest_framework import serializers
from .models import StudyMaterial


class StudyMaterialSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    thumbnail = serializers.FileField(write_only=True, required=False, allow_empty_file=True)
    subject_name = serializers.CharField(source='subject.subject_name', read_only=True)
    subject_code = serializers.CharField(source='subject.subject_code', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    semester_number = serializers.IntegerField(source='semester.semester_number', read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()
    department = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = StudyMaterial
        fields = [
            'id', 'title', 'description', 'department', 'department_name', 'semester',
            'semester_number', 'subject', 'module', 'category', 'file', 'thumbnail',
            'academic_year', 'approval_status',
            'rejection_reason', 'download_count', 'uploaded_at', 'updated_at',
            'subject_name', 'subject_code', 'uploaded_by_name',
        ]
        read_only_fields = [
            'approval_status', 'rejection_reason', 'download_count', 'uploaded_at', 'updated_at',
            'department', 'department_name', 'semester_number', 'subject_name', 'subject_code',
            'uploaded_by_name',
        ]

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by_id:
            return obj.uploaded_by.user.get_full_name() or obj.uploaded_by.user.email
        if obj.created_by_id:
            return obj.created_by.get_full_name() or obj.created_by.email
        return 'Department HOD'

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_hod():
            return attrs
        department_id = user.department_id
        semester = attrs.get('semester', getattr(self.instance, 'semester', None))
        subject = attrs.get('subject', getattr(self.instance, 'subject', None))
        module = attrs.get('module', getattr(self.instance, 'module', None))
        if semester and semester.department_id != department_id:
            raise serializers.ValidationError({'semester': 'Semester must belong to your department.'})
        if subject and subject.department_id != department_id:
            raise serializers.ValidationError({'subject': 'Subject must belong to your department.'})
        if semester and subject and subject.semester_id != semester.id:
            raise serializers.ValidationError({'subject': 'Subject must belong to the selected semester.'})
        if module and (not subject or module.subject_id != subject.id):
            raise serializers.ValidationError({'module': 'Module must belong to the selected subject.'})
        return attrs


class PublicStudyMaterialSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.subject_name', read_only=True)
    subject_code = serializers.CharField(source='subject.subject_code', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)
    semester_number = serializers.IntegerField(source='semester.semester_number', read_only=True)

    class Meta:
        model = StudyMaterial
        fields = [
            'id',
            'title',
            'description',
            'category',
            'academic_year',
            'uploaded_at',
            'download_count',
            'subject_name',
            'subject_code',
            'department_name',
            'department_code',
            'semester_number',
        ]
