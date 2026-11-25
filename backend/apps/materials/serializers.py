from rest_framework import serializers
from apps.accounts.models import TeacherProfile
from apps.teachers.models import TeacherSubjectAssignment
from .models import StudyMaterial


class StudyMaterialSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True, required=False)
    thumbnail = serializers.FileField(write_only=True, required=False, allow_empty_file=True)
    subject_name = serializers.CharField(source='subject.subject_name', read_only=True)
    subject_code = serializers.CharField(source='subject.subject_code', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    semester_number = serializers.IntegerField(source='semester.semester_number', read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()
    department = serializers.PrimaryKeyRelatedField(read_only=True)
    category = serializers.CharField(source='material_type', read_only=True)
    uploaded_at = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = StudyMaterial
        fields = [
            'id', 'title', 'description', 'department', 'department_name', 'semester',
            'semester_number', 'subject', 'module', 'material_type', 'category', 'file', 'thumbnail',
            'academic_year', 'approval_status',
            'rejection_reason', 'download_count', 'created_at', 'uploaded_at', 'updated_at',
            'subject_name', 'subject_code', 'uploaded_by_name',
        ]
        read_only_fields = [
            'approval_status', 'rejection_reason', 'download_count', 'created_at', 'uploaded_at', 'updated_at',
            'department', 'department_name', 'semester_number', 'subject_name', 'subject_code',
            'uploaded_by_name', 'category',
        ]

    def to_internal_value(self, data):
        legacy_value = data.get('material_type', data.get('category'))
        if legacy_value:
            data = data.copy()
            data['material_type'] = {
                'PREVIOUS_PAPER': 'QUESTION_PAPER',
                'MODEL_PAPER': 'QUESTION_PAPER',
                'INTERNAL_PAPER': 'QUESTION_PAPER',
                'PRACTICAL': 'LAB_MANUAL',
                'SYLLABUS': 'OTHER',
                'IMPORTANT_QUESTIONS': 'OTHER',
                'REFERENCE': 'OTHER',
            }.get(legacy_value, legacy_value)
        return super().to_internal_value(data)

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by_id:
            return obj.uploaded_by.user.get_full_name() or obj.uploaded_by.user.email
        if obj.created_by_id:
            return obj.created_by.get_full_name() or obj.created_by.email
        return 'Department HOD'

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if self.instance is None and 'file' not in attrs:
            raise serializers.ValidationError({'file': 'A material file is required.'})
        if not user or not (user.is_hod() or user.is_teacher()):
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
        academic_year = attrs.get('academic_year', getattr(self.instance, 'academic_year', None))
        if semester and academic_year and semester.academic_year != academic_year:
            raise serializers.ValidationError(
                {'academic_year': 'Academic year must match the selected semester.'}
            )
        if user.is_teacher():
            profile = TeacherProfile.objects.filter(
                user=user,
                department_id=department_id,
            ).first()
            if not profile:
                raise serializers.ValidationError('Your teacher profile is not configured correctly.')
            if subject and not TeacherSubjectAssignment.objects.filter(
                teacher=profile,
                subject=subject,
                academic_year=semester.academic_year if semester else academic_year,
            ).exists():
                raise serializers.ValidationError(
                    {'subject': 'You can only upload materials for subjects assigned to you.'}
                )
        return attrs


class PublicStudyMaterialSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.subject_name', read_only=True)
    subject_code = serializers.CharField(source='subject.subject_code', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)
    semester_number = serializers.IntegerField(source='semester.semester_number', read_only=True)
    category = serializers.CharField(source='material_type', read_only=True)
    uploaded_at = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = StudyMaterial
        fields = [
            'id',
            'title',
            'description',
            'material_type',
            'category',
            'academic_year',
            'created_at',
            'uploaded_at',
            'download_count',
            'subject_name',
            'subject_code',
            'department_name',
            'department_code',
            'semester_number',
        ]
