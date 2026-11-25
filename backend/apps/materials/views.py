from django.db import transaction
from django.db.models import F
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.audit import record_audit
from apps.accounts.models import TeacherProfile
from apps.accounts.permissions import IsHod, IsTeacher
from apps.teachers.models import TeacherSubjectAssignment
from apps.notifications.models import Notification
from .models import MaterialApproval, StudyMaterial
from .serializers import PublicStudyMaterialSerializer, StudyMaterialSerializer


class PublicMaterialFilter(filters.FilterSet):
    department_code = filters.CharFilter(field_name='department__code', lookup_expr='iexact')
    department = filters.NumberFilter(field_name='department_id')
    study_year = filters.NumberFilter(method='filter_study_year')
    semester = filters.NumberFilter(field_name='semester__semester_number')
    subject = filters.NumberFilter(field_name='subject_id')
    module = filters.NumberFilter(field_name='module_id')
    material_type = filters.ChoiceFilter(choices=StudyMaterial.MaterialType.choices)
    category = filters.CharFilter(method='filter_legacy_category')

    class Meta:
        model = StudyMaterial
        fields = ['academic_year']

    def filter_study_year(self, queryset, name, value):
        study_year = int(value)
        if study_year not in range(1, 5):
            return queryset.none()
        first_semester = (study_year - 1) * 2 + 1
        return queryset.filter(
            semester__semester_number__gte=first_semester,
            semester__semester_number__lte=first_semester + 1,
        )

    def filter_legacy_category(self, queryset, name, value):
        legacy_categories = {
            'PREVIOUS_PAPER': StudyMaterial.MaterialType.QUESTION_PAPER,
            'MODEL_PAPER': StudyMaterial.MaterialType.QUESTION_PAPER,
            'INTERNAL_PAPER': StudyMaterial.MaterialType.QUESTION_PAPER,
            'PRACTICAL': StudyMaterial.MaterialType.LAB_MANUAL,
            'SYLLABUS': StudyMaterial.MaterialType.OTHER,
            'IMPORTANT_QUESTIONS': StudyMaterial.MaterialType.OTHER,
            'REFERENCE': StudyMaterial.MaterialType.OTHER,
        }
        return queryset.filter(material_type=legacy_categories.get(value, value))


class HodMaterialView(generics.ListCreateAPIView):
    permission_classes = [IsHod]
    serializer_class = StudyMaterialSerializer
    filterset_fields = ['approval_status', 'semester', 'subject', 'module', 'material_type', 'academic_year']
    search_fields = ['title', 'description', 'subject__subject_name', 'subject__subject_code']
    ordering_fields = ['created_at', 'download_count']

    def get_queryset(self):
        return StudyMaterial.objects.filter(
            department_id=self.request.user.department_id,
        ).select_related('subject', 'department', 'semester', 'uploaded_by__user', 'created_by')

    @transaction.atomic
    def perform_create(self, serializer):
        material = serializer.save(
            department=self.request.user.department,
            created_by=self.request.user,
            approval_status=StudyMaterial.Status.APPROVED,
        )
        record_audit(
            self.request,
            'material.created_by_hod',
            details={'material_id': material.pk, 'subject_id': material.subject_id},
        )


class HodMaterialDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsHod]
    serializer_class = StudyMaterialSerializer

    def get_queryset(self):
        return StudyMaterial.objects.filter(
            department_id=self.request.user.department_id,
        ).select_related('subject', 'department', 'semester', 'uploaded_by__user', 'created_by')

    def perform_update(self, serializer):
        material = serializer.save()
        record_audit(
            self.request,
            'material.updated',
            details={'material_id': material.pk},
        )

    def perform_destroy(self, instance):
        instance.approval_status = StudyMaterial.Status.ARCHIVED
        instance.save(update_fields=['approval_status', 'updated_at'])
        record_audit(
            self.request,
            'material.archived',
            details={'material_id': instance.pk},
        )


class ReviewMaterialSerializer(serializers.Serializer):
    rejection_reason = serializers.CharField(required=False, allow_blank=True, max_length=5000)


class ReviewMaterialView(generics.GenericAPIView):
    permission_classes = [IsHod]
    serializer_class = ReviewMaterialSerializer

    def post(self, request, pk):
        action_name = request.path.rstrip('/').split('/')[-1]
        if action_name not in ('approve', 'reject'):
            return Response({'detail': 'Unsupported review action.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('rejection_reason', '').strip()
        if action_name == 'reject' and not reason:
            return Response({'rejection_reason': 'Rejection reason is required.'}, status=400)

        with transaction.atomic():
            material = get_object_or_404(
                StudyMaterial.objects.select_for_update().filter(
                    department_id=request.user.department_id,
                ),
                pk=pk,
            )
            status_value = (
                StudyMaterial.Status.APPROVED
                if action_name == 'approve'
                else StudyMaterial.Status.REJECTED
            )
            material.approval_status = status_value
            material.rejection_reason = reason if status_value == StudyMaterial.Status.REJECTED else ''
            material.save(update_fields=['approval_status', 'rejection_reason', 'updated_at'])
            MaterialApproval.objects.update_or_create(
                material=material,
                defaults={
                    'reviewed_by': request.user,
                    'status': status_value,
                    'rejection_reason': material.rejection_reason,
                },
            )
            if material.uploaded_by_id:
                Notification.objects.create(
                    recipient=material.uploaded_by.user,
                    title=f'Material {status_value.lower()}',
                    message=(
                        reason
                        if status_value == StudyMaterial.Status.REJECTED
                        else f'{material.title} was approved.'
                    ),
                    link=f'/hod/materials/{material.id}',
                )
            record_audit(
                request,
                f'material.{status_value.lower()}',
                details={'material_id': material.pk},
            )
        return Response({'id': material.id, 'approval_status': material.approval_status})


class HodMaterialDownloadView(generics.GenericAPIView):
    permission_classes = [IsHod]

    def get(self, request, pk):
        material = get_object_or_404(
            StudyMaterial.objects.filter(department_id=request.user.department_id),
            pk=pk,
        )
        StudyMaterial.objects.filter(pk=pk).update(download_count=F('download_count') + 1)
        return FileResponse(
            material.file.open('rb'),
            as_attachment=True,
            filename=material.file.name.rsplit('/', 1)[-1],
        )


class PublicMaterialListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PublicStudyMaterialSerializer
    filterset_class = PublicMaterialFilter
    search_fields = ['title', 'description', 'subject__subject_name', 'subject__subject_code']
    ordering_fields = ['created_at', 'download_count']

    def get_queryset(self):
        queryset = StudyMaterial.objects.filter(
            approval_status=StudyMaterial.Status.APPROVED,
        ).select_related('subject', 'department', 'semester')
        legacy_department_code = self.request.query_params.get('department__code')
        if legacy_department_code:
            queryset = queryset.filter(department__code__iexact=legacy_department_code)
        return queryset


class PublicMaterialOptionsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        params = request.query_params.copy()
        params.pop('subject', None)
        params.pop('material_type', None)
        params.pop('category', None)
        material_filter = PublicMaterialFilter(
            data=params,
            queryset=StudyMaterial.objects.filter(
                approval_status=StudyMaterial.Status.APPROVED,
            ).select_related('subject', 'department', 'semester'),
        )
        if not material_filter.is_valid():
            raise serializers.ValidationError(material_filter.errors)
        subjects = material_filter.qs.values(
            'subject_id',
            'subject__subject_name',
            'subject__subject_code',
        ).distinct().order_by('subject__subject_code')
        return Response([
            {
                'id': subject['subject_id'],
                'name': subject['subject__subject_name'],
                'code': subject['subject__subject_code'],
            }
            for subject in subjects
        ])


class TeacherMaterialOptionsView(APIView):
    permission_classes = [IsTeacher]

    def get(self, request):
        profile = get_object_or_404(
            TeacherProfile.objects.select_related('department'),
            user=request.user,
            department_id=request.user.department_id,
        )
        assignments = TeacherSubjectAssignment.objects.filter(
            teacher=profile,
            subject__department_id=profile.department_id,
        ).select_related('subject', 'subject__semester').order_by(
            'subject__semester__semester_number',
            'subject__subject_code',
        )
        return Response({
            'department': {
                'id': profile.department_id,
                'code': profile.department.code,
                'name': profile.department.name,
            },
            'subjects': [
                {
                    'id': assignment.subject_id,
                    'name': assignment.subject.subject_name,
                    'code': assignment.subject.subject_code,
                    'semester': assignment.subject.semester_id,
                    'semester_number': assignment.subject.semester.semester_number,
                    'academic_year': assignment.academic_year,
                }
                for assignment in assignments
            ],
        })


class TeacherMaterialListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsTeacher]
    serializer_class = StudyMaterialSerializer
    filterset_fields = ['approval_status', 'semester', 'subject', 'material_type', 'academic_year']
    search_fields = ['title', 'description', 'subject__subject_name', 'subject__subject_code']
    ordering_fields = ['created_at', 'download_count']

    def get_queryset(self):
        return StudyMaterial.objects.filter(
            uploaded_by__user=self.request.user,
            department_id=self.request.user.department_id,
        ).exclude(
            approval_status=StudyMaterial.Status.ARCHIVED,
        ).select_related('subject', 'department', 'semester', 'uploaded_by__user')

    @transaction.atomic
    def perform_create(self, serializer):
        profile = get_object_or_404(
            TeacherProfile.objects.select_related('department'),
            user=self.request.user,
            department_id=self.request.user.department_id,
        )
        material = serializer.save(
            uploaded_by=profile,
            department=profile.department,
            created_by=None,
            approval_status=StudyMaterial.Status.PENDING,
        )
        record_audit(
            self.request,
            'material.created_by_teacher',
            department=profile.department,
            target_user=self.request.user,
            details={'material_id': material.pk, 'subject_id': material.subject_id},
        )


class TeacherMaterialDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsTeacher]
    serializer_class = StudyMaterialSerializer

    def get_queryset(self):
        return StudyMaterial.objects.filter(
            uploaded_by__user=self.request.user,
            department_id=self.request.user.department_id,
        ).exclude(
            approval_status=StudyMaterial.Status.ARCHIVED,
        ).select_related('subject', 'department', 'semester', 'uploaded_by__user')

    @transaction.atomic
    def perform_update(self, serializer):
        material = serializer.save(
            approval_status=StudyMaterial.Status.PENDING,
            rejection_reason='',
        )
        MaterialApproval.objects.filter(material=material).delete()
        record_audit(
            self.request,
            'material.updated_by_teacher',
            department=self.request.user.department,
            target_user=self.request.user,
            details={'material_id': material.pk},
        )

    @transaction.atomic
    def perform_destroy(self, instance):
        instance.approval_status = StudyMaterial.Status.ARCHIVED
        instance.save(update_fields=['approval_status', 'updated_at'])
        record_audit(
            self.request,
            'material.archived_by_teacher',
            department=self.request.user.department,
            target_user=self.request.user,
            details={'material_id': instance.pk},
        )


class PublicMaterialDownloadView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        material = get_object_or_404(
            StudyMaterial.objects.filter(approval_status=StudyMaterial.Status.APPROVED),
            pk=pk,
        )
        StudyMaterial.objects.filter(pk=pk).update(download_count=F('download_count') + 1)
        return FileResponse(
            material.file.open('rb'),
            as_attachment=True,
            filename=material.file.name.rsplit('/', 1)[-1],
        )


class TeacherMaterialDownloadView(generics.GenericAPIView):
    permission_classes = [IsTeacher]

    def get(self, request, pk):
        material = get_object_or_404(
            StudyMaterial.objects.filter(
                uploaded_by__user=request.user,
                department_id=request.user.department_id,
            ).exclude(approval_status=StudyMaterial.Status.ARCHIVED),
            pk=pk,
        )
        StudyMaterial.objects.filter(pk=pk).update(download_count=F('download_count') + 1)
        return FileResponse(
            material.file.open('rb'),
            as_attachment=True,
            filename=material.file.name.rsplit('/', 1)[-1],
        )
