from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsHod
from apps.accounts.models import User
from apps.academics.models import Department, Semester, Subject, Module
from apps.academics.serializers import DepartmentSerializer, SemesterSerializer, SubjectSerializer, ModuleSerializer
from apps.materials.models import StudyMaterial
from .models import TeacherSubjectAssignment
from .serializers import TeacherCreateSerializer, TeacherSerializer, AssignmentSerializer


class HodTeacherViewSet(viewsets.ModelViewSet):
    permission_classes = [IsHod]
    queryset = User.objects.filter(role=User.Role.TEACHER).select_related('teacher_profile')
    http_method_names = ['get', 'post', 'put', 'patch']

    def get_serializer_class(self):
        return TeacherCreateSerializer if self.action == 'create' else TeacherSerializer

    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        teacher = self.get_object()
        teacher.is_active = bool(request.data.get('is_active', not teacher.is_active))
        teacher.save(update_fields=['is_active'])
        return Response({'id': teacher.id, 'is_active': teacher.is_active})


class DepartmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsHod]
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class SemesterViewSet(viewsets.ModelViewSet):
    permission_classes = [IsHod]
    queryset = Semester.objects.select_related('department')
    serializer_class = SemesterSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsHod]
    queryset = Subject.objects.select_related('department', 'semester')
    serializer_class = SubjectSerializer


class ModuleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsHod]
    queryset = Module.objects.select_related('subject')
    serializer_class = ModuleSerializer


class AssignmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsHod]
    queryset = TeacherSubjectAssignment.objects.select_related('teacher', 'subject')
    serializer_class = AssignmentSerializer


class HodDashboardView(generics.GenericAPIView):
    permission_classes = [IsHod]

    def get(self, request):
        materials = StudyMaterial.objects
        return Response({
            'students': User.objects.filter(role=User.Role.STUDENT).count(),
            'teachers': User.objects.filter(role=User.Role.TEACHER).count(),
            'departments': Department.objects.count(),
            'subjects': Subject.objects.count(),
            'materials': materials.count(),
            'pending_materials': materials.filter(approval_status='PENDING').count(),
            'approved_materials': materials.filter(approval_status='APPROVED').count(),
            'recent_materials': list(materials.select_related('subject', 'uploaded_by__user').values(
                'id', 'title', 'approval_status', 'uploaded_at'
            )[:8]),
        })
