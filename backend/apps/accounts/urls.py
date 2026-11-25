from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView
from .views import (
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    StudentLoginView,
)

urlpatterns = [
    path('logout/', TokenBlacklistView.as_view()),
    path('student/login/', StudentLoginView.as_view()),
    path('password/change/', PasswordChangeView.as_view()),
    path('password/reset/', PasswordResetRequestView.as_view()),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view()),
]
