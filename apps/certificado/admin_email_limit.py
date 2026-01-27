"""
Admin interface mejorado con DailyEmailLimit.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import (
    Direccion,
    PlantillaBase,
    VariantePlantilla,
    Evento,
    Estudiante,
    Certificado,
    ProcesamientoLote,
    DailyEmailLimit
)


# ... (mismo contenido anterior) ...

@admin.register(DailyEmailLimit)
class DailyEmailLimitAdmin(admin.ModelAdmin):
    """
    Admin para límite diario de emails.
    """
    list_display = ['fecha', 'emails_enviados', 'emails_restantes', 'porcentaje_uso', 'ultimo_reset']
    list_filter = ['fecha']
    readonly_fields = ['emails_enviados', 'ultimo_reset', 'emails_restantes_display', 'porcentaje_display']
    ordering = ['-fecha']
    
    fieldsets = (
        ('Información', {
            'fields': ('fecha', 'emails_enviados', 'emails_restantes_display', 'porcentaje_display')
        }),
        ('Metadata', {
            'fields': ('ultimo_reset',)
        }),
    )
    
    def emails_restantes(self, obj):
        """Emails restantes hoy"""
        restantes = DailyEmailLimit.LIMITE_DIARIO - obj.emails_enviados
        if restantes < 50:
            color = 'red'
        elif restantes < 100:
            color = 'orange'
        else:
            color = 'green'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            restantes
        )
    emails_restantes.short_description = 'Restantes'
    
    def porcentaje_uso(self, obj):
        """Porcentaje de uso"""
        porcentaje = (obj.emails_enviados / DailyEmailLimit.LIMITE_DIARIO) * 100
        return f"{porcentaje:.1f}%"
    porcentaje_uso.short_description = 'Uso %'
    
    def emails_restantes_display(self, obj):
        """Display para readonly field"""
        restantes = DailyEmailLimit.LIMITE_DIARIO - obj.emails_enviados
        return f"{restantes} / {DailyEmailLimit.LIMITE_DIARIO}"
    emails_restantes_display.short_description = 'Emails Restantes'
    
    def porcentaje_display(self, obj):
        """Display de porcentaje con barra"""
        porcentaje = (obj.emails_enviados / DailyEmailLimit.LIMITE_DIARIO) * 100
        
        if porcentaje >= 90:
            color = '#dc3545'
        elif porcentaje >= 75:
            color = '#ffc107'
        else:
            color = '#28a745'
        
        return format_html(
            '<div style="width: 200px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; color: white; text-align: center; padding: 5px; border-radius: 3px;">'
            '{:.1f}%'
            '</div>'
            '</div>',
            porcentaje,
            color,
            porcentaje
        )
    porcentaje_display.short_description = 'Porcentaje de Uso'
    
    def has_add_permission(self, request):
        """No permitir creación manual"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminación"""
        return False
