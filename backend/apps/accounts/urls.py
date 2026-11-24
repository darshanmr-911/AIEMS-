from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView

urlpatterns = [
    path('logout/', TokenBlacklistView.as_view()),
]
