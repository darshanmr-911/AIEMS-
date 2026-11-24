from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsHod, IsTeacher
from apps.materials.models import MaterialApproval, StudyMaterial
from apps.notifications.models import Notification
from apps.teachers.models import TeacherSubjectAssignment
from .serializers import StudyMaterialSerializer


class TeacherMaterialListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsTeacher]
    serializer_class = StudyMaterialSerializer

    def get_queryset(self):
        return StudyMaterial.objects.filter(uploaded_by=self.request.user.teacher_profile)

    def perform_create(self, serializer):
        profile = self.request.user.teacher_profile
        subject = serializer.validated_data['subject']
        if not TeacherSubjectAssignment.objects.filter(
            teacher=profile,
            subject=subject,
            academic_year=serializer.validated_data['academic_year'],
        ).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You are not assigned to this subject for the selected academic year.')
        material = serializer.save(uploaded_by=profile)
        for hod in material.uploaded_by.user.__class__.objects.filter(role='HOD'):
            Notification.objects.create(
                recipient=hod,
                title='New material pending approval',
                message=f'{material.title} was uploaded and requires review.',
                link=f'/hod/materials/{material.id}',
            )


class TeacherMaterialDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsTeacher]
    serializer_class = StudyMaterialSerializer

    def get_queryset(self):
        return StudyMaterial.objects.filter(uploaded_by=self.request.user.teacher_profile)

    def perform_update(self, serializer):
        material = serializer.save(approval_status=StudyMaterial.Status.PENDING)
        material.rejection_reason = ''
        material.save(update_fields=['rejection_reason', 'approval_status'])


class HodMaterialView(generics.ListAPIView):
    permission_classes = [IsHod]
    serializer_class = StudyMaterialSerializer
    queryset = StudyMaterial.objects.select_related(
        'subject', 'department', 'semester', 'uploaded_by__user'
    ).all()
    filterset_fields = ['approval_status', 'department', 'semester', 'subject', 'module', 'category', 'academic_year']
    search_fields = ['title', 'description', 'subject__subject_name', 'subject__subject_code']
    ordering_fields = ['uploaded_at', 'download_count']


class ReviewMaterialView(generics.GenericAPIView):
    permission_classes = [IsHod]

    def post(self, request, pk):
        material = get_object_or_404(StudyMaterial, pk=pk)
        action = request.path.rstrip('/').split('/')[-1]
        reason = ''
        with transaction.atomic():
            if action == 'approve':
                material.approval_status = StudyMaterial.Status.APPROVED
                material.rejection_reason = ''
                status_value = StudyMaterial.Status.APPROVED
            else:
                reason = request.data.get('rejection_reason', '').strip()
                if not reason:
                    return Response({'rejection_reason': 'Rejection reason is required.'}, status=400)
                material.approval_status = StudyMaterial.Status.REJECTED
                material.rejection_reason = reason
                status_value = StudyMaterial.Status.REJECTED
            material.save(update_fields=['approval_status', 'rejection_reason'])
            MaterialApproval.objects.update_or_create(
                material=material,
                defaults={
                    'reviewed_by': request.user,
                    'status': status_value,
                    'rejection_reason': material.rejection_reason,
                },
            )
            Notification.objects.create(
                recipient=material.uploaded_by.user,
                title=f'Material {status_value.lower()}',
                message=reason if status_value == StudyMaterial.Status.REJECTED else f'{material.title} was approved.',
                link=f'/teacher/materials/{material.id}',
            )
        return Response({'id': material.id, 'approval_status': material.approval_status})
