"""
Formulario para crear eventos y generar certificados.

Hereda de CoreBaseForm para estilos Tailwind automáticos.
"""

from django import forms
from django.core.exceptions import ValidationError
from apps.core.forms.base_form import CoreBaseForm
from ..models import Direccion, VariantePlantilla


class EventoForm(CoreBaseForm):
    """
    Formulario para capturar información del evento.
    Incluye todos los campos necesarios para reemplazar variables en certificados.
    """
    
    # Choices
    MODALIDAD_CHOICES = [
        ('', '-- Seleccione modalidad --'),
        ('virtual', 'Virtual'),
        ('presencial', 'Presencial'),
        ('hibrido', 'Híbrido'),
    ]
    
    TIPO_CHOICES = [
        ('', '-- Seleccione tipo --'),
        ('curso', 'Curso'),
        ('taller', 'Taller'),
        ('seminario', 'Seminario'),
        ('conferencia', 'Conferencia'),
        ('capacitacion', 'Capacitación'),
        ('diplomado', 'Diplomado'),
        ('otro', 'Otro'),
    ]
    
    # Campos
    direccion_gestion = forms.ModelChoiceField(
        queryset=Direccion.objects.filter(activo=True),
        empty_label='-- Seleccione dirección/gestión --',
        label='Dirección/Gestión',
        widget=forms.Select(attrs={
            'id': 'id_direccion_gestion',
            'hx-get': '/certificados/api/variantes/',
            'hx-trigger': 'change',
            'hx-target': '#variante-container',
        })
    )
    
    variante_plantilla = forms.ModelChoiceField(
        queryset=VariantePlantilla.objects.none(),
        required=False,
        empty_label='-- Usar plantilla base --',
        label='Variante de Plantilla (Opcional)',
        help_text='Si no selecciona una variante, se usará la plantilla base de la dirección',
        widget=forms.Select(attrs={'id': 'id_variante_plantilla'})
    )
    
    modalidad = forms.ChoiceField(
        choices=MODALIDAD_CHOICES,
        label='Modalidad',
        widget=forms.Select()
    )
    
    nombre_evento = forms.CharField(
        max_length=300,
        label='Nombre del Evento',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: Taller de Python Avanzado',
        })
    )
    
    duracion_horas = forms.IntegerField(
        min_value=1,
        label='Duración (horas)',
        widget=forms.NumberInput(attrs={
            'placeholder': 'Ej: 40',
            'min': '1',
        })
    )
    
    fecha_inicio = forms.DateField(
        label='Fecha de Inicio',
        widget=forms.DateInput(attrs={
            'type': 'date',
        })
    )
    
    fecha_fin = forms.DateField(
        label='Fecha de Fin',
        widget=forms.DateInput(attrs={
            'type': 'date',
        })
    )
    
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        label='Tipo',
        widget=forms.Select()
    )
    
    tipo_evento = forms.CharField(
        max_length=200,
        label='Tipo de Evento (Descripción específica)',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: Taller práctico de programación',
        })
    )
    
    fecha_emision = forms.DateField(
        label='Fecha de Emisión',
        widget=forms.DateInput(attrs={
            'type': 'date',
        }),
        help_text='Fecha en que se emiten los certificados'
    )
    
    objetivo_programa = forms.CharField(
        label='Objetivo del Programa',
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Describa los objetivos del programa...',
        })
    )
    
    contenido_programa = forms.CharField(
        label='Contenido del Programa',
        widget=forms.Textarea(attrs={
            'rows': 6,
            'placeholder': 'Describa el contenido y temática del programa...',
        })
    )
    
    def __init__(self, *args, **kwargs):
        """
        Inicialización personalizada.
        Actualiza queryset de variantes si se proporciona direccion_gestion.
        """
        super().__init__(*args, **kwargs)
        
        # Cargar direcciones activas
        self.fields['direccion_gestion'].queryset = Direccion.objects.filter(activo=True).order_by('codigo')
        
        # Si hay initial data con dirección, pre-cargar variantes
        if 'direccion_gestion' in self.initial and self.initial['direccion_gestion']:
            try:
                direccion_id = self.initial['direccion_gestion']
                # Obtener plantilla base de esta dirección
                plantilla_base = PlantillaBase.objects.filter(
                    direccion_id=direccion_id,
                    es_activa=True
                ).first()
                
                if plantilla_base:
                    # Cargar variantes activas de esta plantilla
                    self.fields['variante_plantilla'].queryset = VariantePlantilla.objects.filter(
                        plantilla_base=plantilla_base,
                        activo=True
                    ).order_by('orden', 'nombre')
            except (ValueError, TypeError):
                pass
            self.fields['variante_plantilla'].queryset = VariantePlantilla.objects.filter(
                plantilla_base__direccion=self.instance.direccion_gestion,
                plantilla_base__es_activa=True,
                activo=True
            ).select_related('plantilla_base')
    
    def clean(self):
        """
        Validaciones cross-field.
        """
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        fecha_emision = cleaned_data.get('fecha_emision')
        direccion_gestion = cleaned_data.get('direccion_gestion')
        
        # Validar fecha_fin >= fecha_inicio
        if fecha_inicio and fecha_fin:
            if fecha_fin < fecha_inicio:
                raise ValidationError({
                    'fecha_fin': 'La fecha de fin debe ser posterior o igual a la fecha de inicio.'
                })
        
        # Validar que existe plantilla base para la dirección
        if direccion_gestion:
            from ..models import PlantillaBase
            plantilla_base = PlantillaBase.objects.filter(
                direccion=direccion_gestion,
                es_activa=True
            ).first()
            
            if not plantilla_base:
                raise ValidationError({
                    'direccion_gestion': f'No existe una plantilla base activa para "{direccion_gestion}". '
                                       f'Por favor, configure una plantilla en el admin antes de continuar.'
                })
        
        return cleaned_data
