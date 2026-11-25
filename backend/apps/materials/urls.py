from django.urls import path

from .views import PublicMaterialDownloadView, PublicMaterialListView, PublicMaterialOptionsView

urlpatterns = [
    path('materials/', PublicMaterialListView.as_view(), name='public-material-list'),
    path('materials/options/', PublicMaterialOptionsView.as_view(), name='public-material-options'),
    path(
        'materials/<int:pk>/download/',
        PublicMaterialDownloadView.as_view(),
        name='public-material-download',
    ),
]
