import logging
import smtplib

from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from .audit import audit_department_for_user, record_audit
from .models import User
from .passwords import send_password_reset_email
from .serializers import (
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    StudentLoginSerializer,
    StudentRegistrationSerializer,
    SecureTokenRefreshSerializer,
    TeacherLoginSerializer,
)
from .throttles import LoginRateThrottle, PasswordResetRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken


logger = logging.getLogger(__name__)


class SecureTokenRefreshView(TokenRefreshView):
    serializer_class = SecureTokenRefreshSerializer


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginRateThrottle]

    def get(self, request):
        return Response({'status': 'ok'})

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class StudentLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = StudentLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class TeacherLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = TeacherLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class StudentRegistrationView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = StudentRegistrationSerializer


class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role not in (User.Role.HOD, User.Role.TEACHER, User.Role.STUDENT):
            return Response({'detail': 'Password changes are unavailable for this account.'}, status=403)
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.must_change_password = False
        user.save(update_fields=['password', 'must_change_password'])
        record_audit(
            request,
            'password.changed',
            department=audit_department_for_user(user),
            target_user=user,
        )
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'must_change_password': False,
        })


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(
            email__iexact=serializer.validated_data['email'],
            is_active=True,
        ).exclude(role=User.Role.HOD, department__isnull=True).first()
        if user:
            try:
                send_password_reset_email(user)
            except (OSError, smtplib.SMTPException):
                logger.exception('Password reset email delivery failed.')
                return Response(
                    {'detail': 'Password reset email could not be sent. Please try again later.'},
                    status=503,
                )
        return Response(
            {'detail': 'If an active account uses that email, password reset instructions have been sent.'},
            status=202,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        user.set_password(serializer.validated_data['new_password'])
        user.must_change_password = False
        user.save(update_fields=['password', 'must_change_password'])
        record_audit(
            request,
            'password.reset',
            department=audit_department_for_user(user),
            target_user=user,
            actor=user,
        )
        return Response({'detail': 'Password updated. Sign in with your new password.'})
