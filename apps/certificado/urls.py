"""
URLs para la app de certificados.
"""

from django.urls import path
from .views import (
    CertificadoCreateView,
    ProcesamientoStatusView,
    CertificadoListView,
    get_variantes_api
)

app_name = 'certificado'

urlpatterns = [
    # Vistas principales
    path('crear/', CertificadoCreateView.as_view(), name='crear'),
    path('procesamiento/<int:pk>/status/', ProcesamientoStatusView.as_view(), name='procesamiento_status'),
    path('lista/', CertificadoListView.as_view(), name='lista'),
    
    # API endpoints
    path('api/variantes/<int:direccion_id>/', get_variantes_api, name='get_variantes'),
]
