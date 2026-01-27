"""
Formulario para cargar archivo Excel con estudiantes.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from apps.core.forms.base_form import CoreBaseForm
import openpyxl


class ExcelUploadForm(CoreBaseForm):
    """
    Formulario para cargar archivo Excel con estudiantes.
    
    Formato requerido:
        - Columna 1: NOMBRES COMPLETOS
        - Columna 2: CORREO ELECTRONICO
    """
    
    archivo_excel = forms.FileField(
        label='Archivo Excel (.xlsx, .xls)',
        validators=[FileExtensionValidator(allowed_extensions=['xlsx', 'xls'])],
        help_text='Debe contener dos columnas: NOMBRES COMPLETOS, CORREO ELECTRONICO',
        widget=forms.FileInput(attrs={
            'accept': '.xlsx,.xls',
        })
    )
    
    def clean_archivo_excel(self):
        """
        Validación del archivo Excel.
        """
        archivo = self.cleaned_data.get('archivo_excel')
        
        if not archivo:
            return archivo
        
        # Validar tamaño (máximo 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if archivo.size > max_size:
            raise ValidationError(
                f'El archivo es demasiado grande ({archivo.size / (1024*1024):.2f}MB). '
                f'Tamaño máximo: 5MB.'
            )
        
        # Validar que se puede abrir con openpyxl
        try:
            wb = openpyxl.load_workbook(archivo, read_only=True, data_only=True)
            ws = wb.active
            
            # Validar que tiene datos
            if ws.max_row < 2:  # Header + al menos 1 estudiante
                raise ValidationError(
                    'El archivo Excel está vacío o solo contiene encabezados. '
                    'Debe incluir al menos un estudiante.'
                )
            
            # Leer headers
            headers = []
            for cell in ws[1]:
                if cell.value:
                    headers.append(str(cell.value).strip().upper())
            
            # Validar headers requeridos
            required_headers = ['NOMBRES COMPLETOS', 'CORREO ELECTRONICO']
            missing_headers = []
            
            for required in required_headers:
                if required not in headers:
                    # Intentar match flexible (sin acentos, espacios)
                    flexible_headers = [h.replace('Ó', 'O').replace('É', 'E') for h in headers]
                    flexible_required = required.replace('Ó', 'O').replace('É', 'E')
                    
                    if flexible_required not in flexible_headers:
                        missing_headers.append(required)
            
            if missing_headers:
                raise ValidationError(
                    f'Faltan columnas requeridas: {", ".join(missing_headers)}. '
                    f'Columnas encontradas: {", ".join(headers)}. '
                    f'Asegúrese de que las columnas se llamen exactamente: '
                    f'"NOMBRES COMPLETOS" y "CORREO ELECTRONICO".'
                )
            
            wb.close()
            
            # Reiniciar el puntero del archivo para uso posterior
            archivo.seek(0)
            
        except openpyxl.utils.exceptions.InvalidFileException:
            raise ValidationError(
                'El archivo no es un Excel válido. '
                'Asegúrese de subir un archivo .xlsx o .xls.'
            )
        except Exception as e:
            raise ValidationError(
                f'Error al procesar el archivo Excel: {str(e)}'
            )
        
        return archivo
