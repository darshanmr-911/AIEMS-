from django.urls import path
from .views import (
    StudentBookmarkDeleteView, StudentBookmarkView, StudentDashboardView,
    StudentMaterialDetailView, StudentMaterialDownloadView, StudentMaterialListView,
    StudentSubjectListView,
)

urlpatterns = [
    path('dashboard/', StudentDashboardView.as_view()),
    path('subjects/', StudentSubjectListView.as_view()),
    path('materials/', StudentMaterialListView.as_view()),
    path('materials/<int:pk>/', StudentMaterialDetailView.as_view()),
    path('materials/<int:pk>/download/', StudentMaterialDownloadView.as_view()),
    path('bookmarks/', StudentBookmarkView.as_view()),
    path('bookmarks/<int:pk>/', StudentBookmarkDeleteView.as_view()),
]
