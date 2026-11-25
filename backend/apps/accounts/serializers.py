import binascii

from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.http import urlsafe_base64_decode

from apps.academics.models import Department, Semester
from .models import StudentProfile, User


def build_login_response(user):
    refresh = RefreshToken.for_user(user)
    department = user.department
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'must_change_password': user.must_change_password,
        'user': {
            'id': user.id,
            'name': user.get_full_name() or user.username,
            'email': user.email,
            'role': user.role,
            'department': (
                {'id': department.id, 'code': department.code, 'name': department.name}
                if department else None
            ),
        },
    }


class SecureTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        token = self.token_class(attrs['refresh'])
        user_id = token.get('user_id')
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist as exc:
            raise InvalidToken('Token is no longer valid.') from exc
        if not user.is_active or user.is_teacher():
            raise InvalidToken('Token is no longer valid.')
        return super().validate(attrs)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        account = User.objects.filter(
            email__iexact=attrs['email'],
            role=User.Role.HOD,
            department__isnull=False,
        ).first()
        user = authenticate(
            username=account.username if account else attrs['email'],
            password=attrs['password'],
        )
        if not account or user is None or user.pk != account.pk or not user.is_active:
            raise serializers.ValidationError('Invalid email or password.')
        return build_login_response(user)


class StudentLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user or not user.is_active or not user.is_student():
            raise serializers.ValidationError('Invalid username or password.')
        return build_login_response(user)


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
        if attrs['semester'].department_id != attrs['department'].id:
            raise serializers.ValidationError({'semester': 'Semester must belong to the selected department.'})
        if attrs['email'] and User.objects.filter(email__iexact=attrs['email']).exists():
            raise serializers.ValidationError({'email': 'An account with this email already exists.'})
        try:
            password_validation.validate_password(attrs['password'])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)}) from exc
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


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError({'current_password': 'Current password is incorrect.'})
        if attrs['new_password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        try:
            password_validation.validate_password(attrs['new_password'], user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'new_password': list(exc.messages)}) from exc
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            user_id = urlsafe_base64_decode(attrs['uid']).decode()
            user = User.objects.get(pk=user_id, is_active=True)
        except (binascii.Error, UnicodeDecodeError, OverflowError, TypeError, ValueError, User.DoesNotExist) as exc:
            raise serializers.ValidationError('This password reset link is invalid or has expired.') from exc
        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError('This password reset link is invalid or has expired.')
        if attrs['new_password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        try:
            password_validation.validate_password(attrs['new_password'], user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'new_password': list(exc.messages)}) from exc
        attrs['user'] = user
        return attrs
