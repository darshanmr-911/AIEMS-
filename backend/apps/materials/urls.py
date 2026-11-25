from django.urls import path

from .views import PublicMaterialDownloadView, PublicMaterialListView

urlpatterns = [
    path('materials/', PublicMaterialListView.as_view(), name='public-material-list'),
    path(
        'materials/<int:pk>/download/',
        PublicMaterialDownloadView.as_view(),
        name='public-material-download',
    ),
]
