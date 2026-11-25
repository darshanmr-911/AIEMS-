from django.urls import path

from .views import (
    TeacherMaterialDetailView,
    TeacherMaterialDownloadView,
    TeacherMaterialListCreateView,
    TeacherMaterialOptionsView,
)

urlpatterns = [
    path('materials/options/', TeacherMaterialOptionsView.as_view(), name='teacher-material-options'),
    path('materials/', TeacherMaterialListCreateView.as_view(), name='teacher-material-list'),
    path(
        'materials/<int:pk>/download/',
        TeacherMaterialDownloadView.as_view(),
        name='teacher-material-download',
    ),
    path('materials/<int:pk>/', TeacherMaterialDetailView.as_view(), name='teacher-material-detail'),
]
