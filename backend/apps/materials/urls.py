from django.urls import path
from .views import (
    HodMaterialView, ReviewMaterialView, TeacherMaterialDetailView, TeacherMaterialListCreateView,
)

urlpatterns = [
    path('dashboard/', TeacherMaterialListCreateView.as_view()),
    path('assigned-subjects/', TeacherMaterialListCreateView.as_view()),
    path('materials/', TeacherMaterialListCreateView.as_view()),
    path('materials/<int:pk>/', TeacherMaterialDetailView.as_view()),
]
