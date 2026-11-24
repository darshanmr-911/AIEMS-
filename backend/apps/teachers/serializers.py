from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.accounts.models import TeacherProfile, User
from apps.academics.models import Department
from apps.teachers.models import TeacherSubjectAssignment


class TeacherCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    employee_id = serializers.CharField(write_only=True)
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), write_only=True)
    designation = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'password',
                  'employee_id', 'department', 'designation', 'is_active']
        read_only_fields = ['id', 'is_active']

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc))
        return value

    def create(self, validated_data):
        employee_id = validated_data.pop('employee_id')
        department = validated_data.pop('department')
        designation = validated_data.pop('designation', 'Teacher')
        password = validated_data.pop('password')
        user = User.objects.create_user(
            role=User.Role.TEACHER,
            password=password,
            **validated_data,
        )
        TeacherProfile.objects.create(
            user=user, employee_id=employee_id, department=department, designation=designation
        )
        return user


class TeacherSerializer(serializers.ModelSerializer):
    teacher_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_active', 'teacher_profile']

    def get_teacher_profile(self, obj):
        profile = getattr(obj, 'teacher_profile', None)
        if not profile:
            return None
        return {
            'employee_id': profile.employee_id,
            'department': profile.department_id,
            'department_name': profile.department.name,
            'designation': profile.designation,
        }


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherSubjectAssignment
        fields = '__all__'
