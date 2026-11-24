from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.academics.models import Department, Semester
from .models import StudentProfile, TeacherProfile, User


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user or not user.is_active:
            raise serializers.ValidationError('Invalid credentials or inactive account.')
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'name': user.get_full_name() or user.username,
                'email': user.email,
                'role': user.role,
            },
        }


class StudentRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    usn = serializers.CharField(write_only=True)
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), write_only=True)
    semester = serializers.PrimaryKeyRelatedField(queryset=Semester.objects.all(), write_only=True)
    academic_year = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'password_confirm',
                  'usn', 'department', 'semester', 'academic_year']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        if StudentProfile.objects.filter(usn__iexact=attrs['usn']).exists():
            raise serializers.ValidationError({'usn': 'This USN is already registered.'})
        return attrs

    def create(self, validated_data):
        profile_data = {
            'usn': validated_data.pop('usn'),
            'department': validated_data.pop('department'),
            'semester': validated_data.pop('semester'),
            'academic_year': validated_data.pop('academic_year'),
        }
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, role=User.Role.STUDENT, **validated_data)
        StudentProfile.objects.create(user=user, **profile_data)
        return user
