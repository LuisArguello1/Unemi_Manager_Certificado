"""
Formularios para gestión de direcciones/gestiones institucionales.
"""

from django import forms
from django.core.exceptions import ValidationError
from apps.core.forms.base_form import CoreBaseModelForm
from ..models import Direccion
import re


class DireccionForm(CoreBaseModelForm):
    """
    Formulario para crear/editar Direccion.
    El código se genera automáticamente en el backend.
    """
    
    class Meta:
        model = Direccion
        fields = ['nombre', 'descripcion', 'activo']
        # Widgets removidos para usar estilos base de BaseFormMixin

        labels = {
            'nombre': 'Nombre de la Dirección/Gestión',
            'descripcion': 'Descripción',
            'activo': 'Activa'
        }
        help_texts = {
            'nombre': 'El código se generará automáticamente basado en el nombre',
            'activo': 'Solo las direcciones activas aparecen en los formularios'
        }
    
    def _generar_codigo(self, nombre):
        """
        Genera un código único basado en el nombre.
        
        Reglas:
        - Toma las iniciales de cada palabra
        - Convierte a mayúsculas
        - Si ya existe, agrega un número secuencial
        
        Ejemplos:
        - "Dirección de Vinculación" -> "DV"
        - "Gestión Académica" -> "GA"
        - "Dirección de Vinculación" (duplicado) -> "DV2"
        """
        # Remover artículos y preposiciones comunes
        palabras_ignorar = ['de', 'del', 'la', 'el', 'las', 'los', 'con', 'y', 'e']
        
        # Dividir en palabras y filtrar
        palabras = nombre.split()
        palabras_significativas = [
            p for p in palabras 
            if p.lower() not in palabras_ignorar and len(p) > 0
        ]
        
        # Tomar primera letra de cada palabra significativa
        if palabras_significativas:
            codigo_base = ''.join([p[0].upper() for p in palabras_significativas])
        else:
            # Fallback: usar primeras 3 letras del nombre
            codigo_base = nombre[:3].upper()
        
        # Verificar unicidad
        codigo = codigo_base
        contador = 2
        while Direccion.objects.filter(codigo=codigo).exclude(pk=self.instance.pk).exists():
            codigo = f"{codigo_base}{contador}"
            contador += 1
        
        return codigo
    
    def save(self, commit=True):
        """
        Override save para generar el código automáticamente.
        """
        instance = super().save(commit=False)
        
        # Generar código si no existe o si el nombre cambió
        if not instance.codigo or (self.instance.pk and 'nombre' in self.changed_data):
            instance.codigo = self._generar_codigo(instance.nombre)
        
        if commit:
            instance.save()
        
        return instance
