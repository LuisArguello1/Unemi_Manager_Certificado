"""
Inicialización del paquete de formularios.
"""

from .evento_form import EventoForm
from .excel_upload_form import ExcelUploadForm
from .plantilla_forms import (
    PlantillaBaseForm,
    VariantePlantillaForm,
    VariantePlantillaFormSet
)
from .direccion_form import DireccionForm
from .catalogo_forms import ModalidadForm, TipoForm, TipoEventoForm

__all__ = [
    'EventoForm',
    'ExcelUploadForm',
    'PlantillaBaseForm',
    'VariantePlantillaForm',
    'VariantePlantillaFormSet',
    'DireccionForm',
    'ModalidadForm',
    'TipoForm',
    'TipoEventoForm',
]
