from django.db.models import F
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response

from apps.accounts.permissions import IsStudent
from apps.academics.models import Subject
from apps.academics.serializers import SubjectSerializer
from apps.materials.models import StudyMaterial
from apps.materials.serializers import StudyMaterialSerializer
from .models import Bookmark, DownloadHistory


class StudentDashboardView(generics.GenericAPIView):
    permission_classes = [IsStudent]

    def get(self, request):
        profile = request.user.student_profile
        subjects = Subject.objects.filter(
            department=profile.department,
            semester=profile.semester,
        )
        materials = StudyMaterial.objects.filter(
            approval_status=StudyMaterial.Status.APPROVED,
            department=profile.department,
            semester=profile.semester,
        )
        return Response({
            'department': profile.department.name,
            'semester': profile.semester.semester_number,
            'subjects': SubjectSerializer(subjects, many=True).data,
            'recent_materials': StudyMaterialSerializer(materials[:8], many=True).data,
            'popular_materials': StudyMaterialSerializer(materials.order_by('-download_count')[:8], many=True).data,
        })


class StudentSubjectListView(generics.ListAPIView):
    permission_classes = [IsStudent]
    serializer_class = SubjectSerializer

    def get_queryset(self):
        profile = self.request.user.student_profile
        return Subject.objects.filter(department=profile.department, semester=profile.semester)


class StudentMaterialListView(generics.ListAPIView):
    permission_classes = [IsStudent]
    serializer_class = StudyMaterialSerializer
    filterset_fields = ['department', 'semester', 'subject', 'module', 'material_type', 'academic_year']
    search_fields = ['title', 'description', 'subject__subject_name', 'subject__subject_code']
    ordering_fields = ['created_at', 'download_count']

    def get_queryset(self):
        return StudyMaterial.objects.filter(
            approval_status=StudyMaterial.Status.APPROVED,
            department=self.request.user.student_profile.department,
        )


class StudentMaterialDetailView(generics.RetrieveAPIView):
    permission_classes = [IsStudent]
    serializer_class = StudyMaterialSerializer

    def get_queryset(self):
        return StudyMaterial.objects.filter(
            approval_status=StudyMaterial.Status.APPROVED,
            department=self.request.user.student_profile.department,
        )


class StudentMaterialDownloadView(generics.GenericAPIView):
    permission_classes = [IsStudent]

    def get(self, request, pk):
        material = get_object_or_404(
            StudyMaterial,
            pk=pk,
            approval_status=StudyMaterial.Status.APPROVED,
            department=request.user.student_profile.department,
        )
        DownloadHistory.objects.create(student=request.user.student_profile, material=material)
        StudyMaterial.objects.filter(pk=pk).update(download_count=F('download_count') + 1)
        return FileResponse(material.file.open('rb'), as_attachment=True, filename=material.file.name)


class StudentBookmarkView(generics.ListCreateAPIView):
    permission_classes = [IsStudent]

    def get_queryset(self):
        return Bookmark.objects.filter(student=self.request.user.student_profile)

    def get_serializer_class(self):
        from rest_framework import serializers
        class BookmarkSerializer(serializers.ModelSerializer):
            material_detail = StudyMaterialSerializer(source='material', read_only=True)
            class Meta:
                model = Bookmark
                fields = ['id', 'material', 'material_detail', 'created_at']
        return BookmarkSerializer

    def perform_create(self, serializer):
        serializer.save(student=self.request.user.student_profile)


class StudentBookmarkDeleteView(generics.DestroyAPIView):
    permission_classes = [IsStudent]

    def get_queryset(self):
        return Bookmark.objects.filter(student=self.request.user.student_profile)
