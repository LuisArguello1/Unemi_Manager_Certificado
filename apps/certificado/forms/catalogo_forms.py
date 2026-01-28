"""
Formularios para gestión de catálogos (Modalidad, Tipo, TipoEvento).
"""

from django import forms
from apps.core.forms.base_form import CoreBaseModelForm
from ..models import Modalidad, Tipo, TipoEvento

class CatalogoBaseForm(CoreBaseModelForm):
    """
    Clase base para formularios de catálogo con generación automática de código.
    """
    def _generar_codigo(self, nombre, model_class):
        """
        Genera un código único basado en el nombre.
        """
        # Remover artículos y preposiciones comunes
        palabras_ignorar = ['de', 'del', 'la', 'el', 'las', 'los', 'con', 'y', 'e', 'en', 'para']
        
        # Dividir en palabras y filtrar
        palabras = nombre.split()
        palabras_significativas = [
            p for p in palabras 
            if p.lower() not in palabras_ignorar and len(p) > 0
        ]
        
        # Tomar primera letra de cada palabra significativa (hasta 3 letras si es una sola palabra)
        if len(palabras_significativas) == 1:
            codigo_base = palabras_significativas[0][:3].upper()
        elif palabras_significativas:
            codigo_base = ''.join([p[0].upper() for p in palabras_significativas])
        else:
            codigo_base = nombre[:3].upper()
        
        # Verificar unicidad
        codigo = codigo_base
        contador = 2
        while model_class.objects.filter(codigo=codigo).exclude(pk=self.instance.pk).exists():
            codigo = f"{codigo_base}{contador}"
            contador += 1
        
        return codigo

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.codigo or (self.instance.pk and 'nombre' in self.changed_data):
            instance.codigo = self._generar_codigo(instance.nombre, self._meta.model)
        
        if commit:
            instance.save()
        return instance


class ModalidadForm(CatalogoBaseForm):
    class Meta:
        model = Modalidad
        fields = ['nombre', 'activo']
        # Widgets removidos para usar estilos base de BaseFormMixin

        labels = {
            'nombre': 'Nombre de la Modalidad',
            'activo': 'Activa'
        }


class TipoForm(CatalogoBaseForm):
    class Meta:
        model = Tipo
        fields = ['nombre', 'activo']
        # Widgets removidos para usar estilos base de BaseFormMixin

        labels = {
            'nombre': 'Nombre del Tipo',
            'activo': 'Activo'
        }


class TipoEventoForm(CatalogoBaseForm):
    class Meta:
        model = TipoEvento
        fields = ['nombre', 'activo']
        # Widgets removidos para usar estilos base de BaseFormMixin

        labels = {
            'nombre': 'Descripción del Tipo de Evento',
            'activo': 'Activo'
        }
