from django.db import transaction
from django.db.models import F
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response

from apps.accounts.audit import record_audit
from apps.accounts.permissions import IsHod
from apps.notifications.models import Notification
from .models import MaterialApproval, StudyMaterial
from .serializers import PublicStudyMaterialSerializer, StudyMaterialSerializer


class HodMaterialView(generics.ListCreateAPIView):
    permission_classes = [IsHod]
    serializer_class = StudyMaterialSerializer
    filterset_fields = ['approval_status', 'semester', 'subject', 'module', 'category', 'academic_year']
    search_fields = ['title', 'description', 'subject__subject_name', 'subject__subject_code']
    ordering_fields = ['uploaded_at', 'download_count']

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
    filterset_fields = {
        'department': ['exact'],
        'department__code': ['exact'],
        'semester': ['exact'],
        'subject': ['exact'],
        'module': ['exact'],
        'category': ['exact'],
        'academic_year': ['exact'],
    }
    search_fields = ['title', 'description', 'subject__subject_name', 'subject__subject_code']
    ordering_fields = ['uploaded_at', 'download_count']

    def get_queryset(self):
        return StudyMaterial.objects.filter(
            approval_status=StudyMaterial.Status.APPROVED,
        ).select_related('subject', 'department', 'semester')


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
