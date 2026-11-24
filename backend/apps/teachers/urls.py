from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    AssignmentViewSet, DepartmentViewSet, HodDashboardView, HodTeacherViewSet,
    ModuleViewSet, SemesterViewSet, SubjectViewSet,
)
from apps.materials.views import HodMaterialView, ReviewMaterialView

router = DefaultRouter()
router.register('teachers', HodTeacherViewSet, basename='hod-teacher')
router.register('departments', DepartmentViewSet, basename='hod-department')
router.register('semesters', SemesterViewSet, basename='hod-semester')
router.register('subjects', SubjectViewSet, basename='hod-subject')
router.register('modules', ModuleViewSet, basename='hod-module')
router.register('assignments', AssignmentViewSet, basename='hod-assignment')

urlpatterns = [
    path('dashboard/', HodDashboardView.as_view()),
    path('materials/', HodMaterialView.as_view()),
    path('materials/<int:pk>/approve/', ReviewMaterialView.as_view()),
    path('materials/<int:pk>/reject/', ReviewMaterialView.as_view()),
] + router.urls
