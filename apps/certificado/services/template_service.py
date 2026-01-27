"""
Servicio para procesar plantillas de certificado.

Carga plantillas Word, inyecta variables y genera documentos.
"""

import os
import logging
from typing import Dict
from docx import Document
from django.conf import settings


logger = logging.getLogger(__name__)


class TemplateService:
    """
    Servicio para procesar plantillas de certificado.
    
    Responsabilidades:
    - Cargar plantillas Word
    - Inyectar variables
    - Generar documentos DOCX
    """
    
    @staticmethod
    def generate_docx(template_path: str, variables: Dict[str, str], output_path: str) -> str:
        """
        Genera un documento DOCX desde una plantilla con variables reemplazadas.
        
        Args:
            template_path: Ruta absoluta a la plantilla .docx
            variables: Diccionario de variables a reemplazar
            output_path: Ruta donde guardar el documento generado
        
        Returns:
            Ruta absoluta del archivo generado
        
        Raises:
            FileNotFoundError: Si la plantilla no existe
            Exception: Si hay error al generar el documento
        
        Ejemplo:
            >>> from apps.certificado.services.template_service import TemplateService
            >>> variables = {
            ...     "NOMBRES": "Juan Pérez",
            ...     "MODALIDAD": "Virtual",
            ...     "NOMBRE_EVENTO": "Taller Python",
            ...     "DURACION": "40 horas"
            ... }
            >>> output = TemplateService.generate_docx(
            ...     '/path/to/template.docx',
            ...     variables,
            ...     '/path/to/output.docx'
            ... )
            >>> print(output)  # /path/to/output.docx
        """
        try:
            # Validar que existe la plantilla
            if not os.path.exists(template_path):
                raise FileNotFoundError(f"Plantilla no encontrada: {template_path}")
            
            logger.info(f"Generando DOCX desde plantilla: {template_path}")
            
            # Importar utilidad de reemplazo
            from ..utils.variable_replacer import replace_variables_in_template
            
            # Cargar y procesar plantilla
            doc = replace_variables_in_template(template_path, variables)
            
            # Asegurar que existe el directorio de salida
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"Directorio creado: {output_dir}")
            
            # Guardar documento
            doc.save(output_path)
            logger.info(f"DOCX generado exitosamente: {output_path}")
            
            # Validar que se creó el archivo
            if not os.path.exists(output_path):
                raise Exception(f"El archivo no se generó correctamente: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error al generar DOCX: {str(e)}")
            raise
    
    @staticmethod
    def get_variables_from_evento_estudiante(evento, estudiante) -> Dict[str, str]:
        """
        Construye el diccionario de variables desde un Evento y Estudiante.
        
        Args:
            evento: Instancia del modelo Evento
            estudiante: Instancia del modelo Estudiante
        
        Returns:
            Diccionario con todas las variables universales
        
        Ejemplo:
            >>> evento = Evento.objects.get(id=1)
            >>> estudiante = Estudiante.objects.get(id=1)
            >>> variables = TemplateService.get_variables_from_evento_estudiante(evento, estudiante)
            >>> print(variables)
            {
                'NOMBRES': 'Juan Pérez',
                'MODALIDAD': 'Virtual',
                ...
            }
        """
        # Formatear fechas
        fecha_inicio_str = evento.fecha_inicio.strftime('%d de %B de %Y') if evento.fecha_inicio else ''
        fecha_fin_str = evento.fecha_fin.strftime('%d de %B de %Y') if evento.fecha_fin else ''
        fecha_emision_str = evento.fecha_emision.strftime('%d de %B de %Y') if evento.fecha_emision else ''
        
        # Construir diccionario con todas las variables universales
        variables = {
            'NOMBRES': estudiante.nombres_completos,
            'MODALIDAD': evento.get_modalidad_display(),
            'NOMBRE_EVENTO': evento.nombre_evento,
            'DURACION': f'{evento.duracion_horas} horas',
            'FECHA_INICIO': fecha_inicio_str,
            'FECHA_FIN': fecha_fin_str,
            'TIPO': evento.get_tipo_display(),
            'TIPO_EVENTO': evento.tipo_evento,
            'FECHA_EMISION': fecha_emision_str,
            'OBJETIVO_PROGRAMA': evento.objetivo_programa,
            'CONTENIDO': evento.contenido_programa,
        }
        
        logger.debug(f"Variables construidas para estudiante {estudiante.id}: {list(variables.keys())}")
        return variables
