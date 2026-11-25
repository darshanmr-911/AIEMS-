from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from apps.accounts.models import TeacherProfile, User
from apps.academics.models import Module, Semester, Subject
from .models import TeacherSubjectAssignment


class TeacherCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    employee_id = serializers.CharField(write_only=True)
    designation = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'password',
            'password_confirm',
            'employee_id',
            'designation',
            'is_active',
        ]
        read_only_fields = ['id', 'is_active']

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value, role__in=[User.Role.HOD, User.Role.TEACHER]).exists():
            raise serializers.ValidationError('A staff account with this email already exists.')
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('This email is already in use as a username.')
        return value.lower()

    def validate_employee_id(self, value):
        if TeacherProfile.objects.filter(employee_id__iexact=value).exists():
            raise serializers.ValidationError('This employee ID is already in use.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        password_user = User(
            username=attrs['email'],
            email=attrs['email'],
            first_name=attrs.get('first_name', ''),
            last_name=attrs.get('last_name', ''),
        )
        try:
            password_validation.validate_password(attrs['password'], password_user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)}) from exc
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        employee_id = validated_data.pop('employee_id')
        designation = validated_data.pop('designation', 'Teacher')
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        email = validated_data['email']
        department = self.context['request'].user.department
        user = User(username=email, role=User.Role.TEACHER, department=department, **validated_data)
        user.set_password(password)
        user.must_change_password = True
        user.save()
        TeacherProfile.objects.create(
            user=user,
            employee_id=employee_id,
            department=department,
            designation=designation,
        )
        return user


class TeacherSerializer(serializers.ModelSerializer):
    teacher_profile_id = serializers.IntegerField(source='teacher_profile.id', read_only=True)
    employee_id = serializers.CharField(source='teacher_profile.employee_id', required=False)
    designation = serializers.CharField(source='teacher_profile.designation', required=False)
    department = serializers.IntegerField(source='department_id', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    assigned_subjects = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'is_active',
            'teacher_profile_id',
            'employee_id',
            'designation',
            'department',
            'department_name',
            'assigned_subjects',
        ]
        read_only_fields = ['id', 'is_active', 'department', 'department_name', 'assigned_subjects']

    def validate_email(self, value):
        if User.objects.filter(
            email__iexact=value,
            role__in=[User.Role.HOD, User.Role.TEACHER],
        ).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('A staff account with this email already exists.')
        return value.lower()

    def validate(self, attrs):
        profile_data = attrs.get('teacher_profile', {})
        employee_id = profile_data.get('employee_id')
        if employee_id and TeacherProfile.objects.filter(
            employee_id__iexact=employee_id,
        ).exclude(pk=self.instance.teacher_profile.pk).exists():
            raise serializers.ValidationError({'employee_id': 'This employee ID is already in use.'})
        return attrs

    def get_assigned_subjects(self, obj):
        profile = getattr(obj, 'teacher_profile', None)
        if profile is None:
            return []
        assignments = profile.subject_assignments.select_related('subject', 'subject__semester').all()
        return [
            {
                'id': assignment.id,
                'subject_id': assignment.subject_id,
                'subject_name': assignment.subject.subject_name,
                'subject_code': assignment.subject.subject_code,
                'semester_id': assignment.subject.semester_id,
                'semester_number': assignment.subject.semester.semester_number,
                'academic_year': assignment.academic_year,
            }
            for assignment in assignments
        ]

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('teacher_profile', {})
        old_email = instance.email
        for field in ('first_name', 'last_name', 'email'):
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        if 'email' in validated_data and instance.username.casefold() == old_email.casefold():
            instance.username = validated_data['email']
        instance.save()
        if profile_data:
            TeacherProfile.objects.filter(user=instance).update(**profile_data)
        return instance


class AssignmentSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()
    subject_name = serializers.CharField(source='subject.subject_name', read_only=True)
    subject_code = serializers.CharField(source='subject.subject_code', read_only=True)
    semester_number = serializers.IntegerField(source='subject.semester.semester_number', read_only=True)

    class Meta:
        model = TeacherSubjectAssignment
        fields = [
            'id',
            'teacher',
            'teacher_name',
            'subject',
            'subject_name',
            'subject_code',
            'semester_number',
            'academic_year',
        ]

    def get_teacher_name(self, obj):
        return obj.teacher.user.get_full_name() or obj.teacher.user.email

    def validate(self, attrs):
        request = self.context['request']
        teacher = attrs.get('teacher', getattr(self.instance, 'teacher', None))
        subject = attrs.get('subject', getattr(self.instance, 'subject', None))
        if teacher and teacher.department_id != request.user.department_id:
            raise serializers.ValidationError({'teacher': 'Teacher must belong to your department.'})
        if subject and subject.department_id != request.user.department_id:
            raise serializers.ValidationError({'subject': 'Subject must belong to your department.'})
        if teacher and not teacher.user.is_active:
            raise serializers.ValidationError({'teacher': 'Inactive teachers cannot receive assignments.'})
        academic_year = attrs.get('academic_year', getattr(self.instance, 'academic_year', None))
        if subject and academic_year != subject.semester.academic_year:
            raise serializers.ValidationError(
                {'academic_year': 'Academic year must match the subject semester.'}
            )
        return attrs


class HodSemesterSerializer(serializers.ModelSerializer):
    department = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Semester
        fields = ['id', 'semester_number', 'department', 'academic_year']

    def create(self, validated_data):
        return Semester.objects.create(department=self.context['request'].user.department, **validated_data)


class HodSubjectSerializer(serializers.ModelSerializer):
    department = serializers.PrimaryKeyRelatedField(read_only=True)
    semester = serializers.PrimaryKeyRelatedField(queryset=Semester.objects.all())

    class Meta:
        model = Subject
        fields = ['id', 'subject_name', 'subject_code', 'department', 'semester']

    def validate_semester(self, value):
        if value.department_id != self.context['request'].user.department_id:
            raise serializers.ValidationError('Semester must belong to your department.')
        return value

    def create(self, validated_data):
        return Subject.objects.create(
            department=self.context['request'].user.department,
            **validated_data,
        )


class HodModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ['id', 'module_number', 'module_name', 'subject']

    def validate_subject(self, value):
        if value.department_id != self.context['request'].user.department_id:
            raise serializers.ValidationError('Subject must belong to your department.')
        return value


class HodProfileSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'department_name', 'department_code']
        read_only_fields = ['id', 'email', 'department_name', 'department_code']
