from rest_framework import generics, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.audit import record_audit
from apps.accounts.models import AuditLog, StudentProfile, TeacherProfile, User
from apps.accounts.passwords import send_password_reset_email
from apps.accounts.permissions import IsHod
from apps.academics.models import Department, Module, Semester, Subject
from apps.academics.serializers import DepartmentSerializer
from apps.materials.models import StudyMaterial
from .models import TeacherSubjectAssignment
from .serializers import (
    AssignmentSerializer,
    HodModuleSerializer,
    HodProfileSerializer,
    HodSemesterSerializer,
    HodSubjectSerializer,
    TeacherCreateSerializer,
    TeacherSerializer,
)

class TeacherUploadHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyMaterial
        fields = ['id', 'title', 'category', 'approval_status', 'uploaded_at', 'download_count']


class TeacherStatusSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()


class HodTeacherViewSet(viewsets.ModelViewSet):
    permission_classes = [IsHod]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']
    search_fields = ['first_name', 'last_name', 'email', 'teacher_profile__employee_id']
    filterset_fields = ['is_active', 'teacher_profile__subject_assignments__subject']

    def get_queryset(self):
        queryset = User.objects.filter(
            role=User.Role.TEACHER,
            department_id=self.request.user.department_id,
            teacher_profile__department_id=self.request.user.department_id,
        ).select_related('department', 'teacher_profile__department').prefetch_related(
            'teacher_profile__subject_assignments__subject__semester'
        ).distinct()
        subject_id = self.request.query_params.get('subject')
        if subject_id:
            queryset = queryset.filter(
                teacher_profile__subject_assignments__subject_id=subject_id,
                teacher_profile__subject_assignments__subject__department_id=self.request.user.department_id,
            )
        return queryset

    def get_serializer_class(self):
        return TeacherCreateSerializer if self.action == 'create' else TeacherSerializer

    def perform_create(self, serializer):
        teacher = serializer.save()
        record_audit(
            self.request,
            'teacher.created',
            target_user=teacher,
            details={'employee_id': teacher.teacher_profile.employee_id},
        )

    def perform_update(self, serializer):
        teacher = serializer.save()
        record_audit(self.request, 'teacher.updated', target_user=teacher)

    def destroy(self, request, *args, **kwargs):
        teacher = self.get_object()
        teacher.is_active = False
        teacher.save(update_fields=['is_active'])
        record_audit(request, 'teacher.deactivated', target_user=teacher)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='uploads')
    def uploads(self, request, pk=None):
        teacher = self.get_object()
        materials = StudyMaterial.objects.filter(
            department_id=request.user.department_id,
            uploaded_by__user=teacher,
        ).order_by('-uploaded_at')[:50]
        serializer = TeacherUploadHistorySerializer(materials, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        serializer = TeacherStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        teacher = self.get_object()
        teacher.is_active = serializer.validated_data['is_active']
        teacher.save(update_fields=['is_active'])
        record_audit(
            request,
            'teacher.activated' if teacher.is_active else 'teacher.deactivated',
            target_user=teacher,
        )
        return Response({'id': teacher.id, 'is_active': teacher.is_active})

    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        teacher = self.get_object()
        if not teacher.email:
            return Response(
                {'detail': 'Add a teacher email address before sending a reset link.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            send_password_reset_email(teacher)
        except (OSError, smtplib.SMTPException):
            return Response(
                {'detail': 'Password reset email could not be sent. Please try again later.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        teacher.must_change_password = True
        teacher.save(update_fields=['must_change_password'])
        record_audit(request, 'teacher.password_reset_requested', target_user=teacher)
        return Response({'detail': 'Password reset instructions sent to the teacher email.'})


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsHod]
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        return Department.objects.filter(pk=self.request.user.department_id)


class SemesterViewSet(viewsets.ModelViewSet):
    permission_classes = [IsHod]
    serializer_class = HodSemesterSerializer

    def get_queryset(self):
        return Semester.objects.filter(
            department_id=self.request.user.department_id
        ).select_related('department')


class SubjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsHod]
    serializer_class = HodSubjectSerializer

    def get_queryset(self):
        return Subject.objects.filter(
            department_id=self.request.user.department_id
        ).select_related('department', 'semester')

    def perform_create(self, serializer):
        subject = serializer.save()
        record_audit(
            self.request,
            'subject.created',
            details={'subject_id': subject.pk, 'subject_code': subject.subject_code},
        )

    def perform_update(self, serializer):
        subject = serializer.save()
        record_audit(self.request, 'subject.updated', details={'subject_id': subject.pk})


class ModuleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsHod]
    serializer_class = HodModuleSerializer

    def get_queryset(self):
        return Module.objects.filter(
            subject__department_id=self.request.user.department_id
        ).select_related('subject')


class AssignmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsHod]
    serializer_class = AssignmentSerializer

    def get_queryset(self):
        return TeacherSubjectAssignment.objects.filter(
            teacher__department_id=self.request.user.department_id,
            teacher__user__department_id=self.request.user.department_id,
            subject__department_id=self.request.user.department_id,
        ).select_related('teacher__user', 'subject', 'subject__semester')

    def perform_create(self, serializer):
        assignment = serializer.save()
        record_audit(
            self.request,
            'assignment.created',
            target_user=assignment.teacher.user,
            details={
                'assignment_id': assignment.pk,
                'subject_id': assignment.subject_id,
                'academic_year': assignment.academic_year,
            },
        )

    def perform_update(self, serializer):
        assignment = serializer.save()
        record_audit(
            self.request,
            'assignment.updated',
            target_user=assignment.teacher.user,
            details={'assignment_id': assignment.pk, 'subject_id': assignment.subject_id},
        )

    def perform_destroy(self, instance):
        record_audit(
            self.request,
            'assignment.deleted',
            target_user=instance.teacher.user,
            details={'assignment_id': instance.pk, 'subject_id': instance.subject_id},
        )
        instance.delete()


class HodAccountView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsHod]
    serializer_class = HodProfileSerializer

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        user = serializer.save()
        record_audit(self.request, 'account.profile_updated', target_user=user)


class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()
    target_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = ['id', 'action', 'actor_name', 'target_name', 'details', 'created_at']

    def get_actor_name(self, obj):
        return obj.actor.get_full_name() or obj.actor.email

    def get_target_name(self, obj):
        if not obj.target_user:
            return ''
        return obj.target_user.get_full_name() or obj.target_user.email


class HodAuditLogView(generics.ListAPIView):
    permission_classes = [IsHod]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        return AuditLog.objects.filter(
            department_id=self.request.user.department_id,
        ).select_related('actor', 'target_user')


class HodDashboardView(generics.GenericAPIView):
    permission_classes = [IsHod]

    def get(self, request):
        department = request.user.department
        teacher_profiles = TeacherProfile.objects.filter(
            department=department,
            user__department=department,
        )
        materials = StudyMaterial.objects.filter(department=department)
        activities = AuditLog.objects.filter(department=department).select_related(
            'actor', 'target_user'
        )[:8]
        recent_activity = [
            {
                'id': event.id,
                'action': event.action,
                'actor': event.actor.get_full_name() or event.actor.email,
                'target': (
                    event.target_user.get_full_name() or event.target_user.email
                    if event.target_user else ''
                ),
                'created_at': event.created_at,
                'details': event.details,
            }
            for event in activities
        ]
        recent_materials = materials.select_related(
            'subject', 'uploaded_by__user', 'created_by'
        )[:8]
        recent_material_data = [
            {
                'id': material.id,
                'title': material.title,
                'approval_status': material.approval_status,
                'uploaded_at': material.uploaded_at,
                'uploaded_by_name': (
                    material.uploaded_by.user.get_full_name()
                    if material.uploaded_by_id
                    else material.created_by.get_full_name() if material.created_by_id else 'Department HOD'
                ),
                'subject_name': material.subject.subject_name,
            }
            for material in recent_materials
        ]
        return Response({
            'department': {
                'id': department.id,
                'name': department.name,
                'code': department.code,
            },
            'hod': {'email': request.user.email, 'name': request.user.get_full_name()},
            'students': StudentProfile.objects.filter(department=department).count(),
            'teachers': teacher_profiles.count(),
            'assigned_subjects': TeacherSubjectAssignment.objects.filter(
                teacher__in=teacher_profiles,
                subject__department=department,
            ).count(),
            'subjects': Subject.objects.filter(department=department).count(),
            'materials': materials.count(),
            'total_uploaded_materials': materials.count(),
            'pending_materials': materials.filter(
                approval_status=StudyMaterial.Status.PENDING
            ).count(),
            'approved_materials': materials.filter(
                approval_status=StudyMaterial.Status.APPROVED
            ).count(),
            'recent_materials': recent_material_data,
            'recent_teacher_activity': recent_activity,
        })
