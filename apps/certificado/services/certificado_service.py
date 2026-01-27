"""
Servicio principal para orquestar la generación masiva de certificados.

Este es el servicio de alto nivel que coordina todo el flujo.
"""

import logging
from typing import Dict, List
from django.db import transaction
from django.utils import timezone
from ..models import Evento, Estudiante, Certificado, ProcesamientoLote
from ..utils import parse_excel_estudiantes


logger = logging.getLogger(__name__)


class CertificadoService:
    """
    Servicio orquestador principal para generación masiva de certificados.
    
    Responsabilidades:
    - Crear registro de Evento
    - Parsear Excel
    - Crear registros de Estudiantes
    - Crear registros de Certificados (estado='pending')
    - Crear ProcesamientoLote
    - Encolar tareas Celery
    """
    
    @staticmethod
    @transaction.atomic
    def process_bulk_certificates(evento_data: Dict, excel_file, user) -> ProcesamientoLote:
        """
        Procesa la generación masiva de certificados.
        
        Este método es transaccional: si algo falla, se hace rollback de todo.
        
        Args:
            evento_data: Diccionario con datos del evento (del EventoForm.cleaned_data)
            excel_file: Archivo Excel subido (UploadedFile de Django)
            user: Usuario que crea el evento
        
        Returns:
            Instancia de ProcesamientoLote creada
        
        Raises:
            Exception: Si hay algún error en el proceso
        
        Ejemplo:
            >>> from apps.certificado.services.certificado_service import CertificadoService
            >>> lote = CertificadoService.process_bulk_certificates(
            ...     evento_data=form.cleaned_data,
            ...     excel_file=request.FILES['archivo_excel'],
            ...     user=request.user
            ... )
            >>> print(lote.id)  # ID del lote creado
        """
        try:
            logger.info("Iniciando procesamiento masivo de certificados")
            
            # 1. Parsear Excel
            logger.info("Parseando archivo Excel...")
            estudiantes_data = parse_excel_estudiantes(excel_file)
            num_estudiantes = len(estudiantes_data)
            logger.info(f"Excel parseado: {num_estudiantes} estudiante(s) encontrado(s)")
            
            if num_estudiantes == 0:
                raise ValueError("El archivo Excel no contiene estudiantes")
            
            # 2. Verificar límite diario de emails (400/día)
            from ..models import DailyEmailLimit
            puede_enviar, restantes, mensaje = DailyEmailLimit.puede_enviar_lote(num_estudiantes)
            
            if not puede_enviar:
                raise ValueError(mensaje)
            
            logger.info(f"Verificación de límite de emails: OK. {mensaje}")
            
            # 2. Crear Evento
            logger.info("Creando registro de Evento...")
            evento = Evento.objects.create(
                direccion=evento_data['direccion_gestion'],
                plantilla_seleccionada=evento_data.get('variante_plantilla'),
                created_by=user,
                modalidad=evento_data['modalidad'],
                nombre_evento=evento_data['nombre_evento'],
                duracion_horas=evento_data['duracion_horas'],
                fecha_inicio=evento_data['fecha_inicio'],
                fecha_fin=evento_data['fecha_fin'],
                tipo=evento_data['tipo'],
                tipo_evento=evento_data['tipo_evento'],
                fecha_emision=evento_data['fecha_emision'],
                objetivo_programa=evento_data['objetivo_programa'],
                contenido_programa=evento_data['contenido_programa'],
            )
            logger.info(f"Evento creado: ID={evento.id}, Nombre={evento.nombre_evento}")
            
            # 3. Crear Estudiantes en bulk
            logger.info("Creando registros de Estudiantes...")
            estudiantes_to_create = [
                Estudiante(
                    evento=evento,
                    nombres_completos=est_data['nombres_completos'],
                    correo_electronico=est_data['correo_electronico']
                )
                for est_data in estudiantes_data
            ]
            estudiantes_created = Estudiante.objects.bulk_create(estudiantes_to_create)
            logger.info(f"{len(estudiantes_created)} estudiante(s) creado(s)")
            
            # 4. Crear Certificados en bulk (estado='pending')
            logger.info("Creando registros de Certificados...")
            certificados_to_create = [
                Certificado(
                    evento=evento,
                    estudiante=estudiante,
                    estado='pending'
                )
                for estudiante in estudiantes_created
            ]
            certificados_created = Certificado.objects.bulk_create(certificados_to_create)
            logger.info(f"{len(certificados_created)} certificado(s) creado(s) en estado 'pending'")
            
            # 5. Crear ProcesamientoLote
            logger.info("Creando registro de Procesamiento en Lote...")
            procesamiento_lote = ProcesamientoLote.objects.create(
                evento=evento,
                total_estudiantes=num_estudiantes,
                procesados=0,
                exitosos=0,
                fallidos=0,
                estado='pending',
                fecha_inicio=timezone.now()
            )
            logger.info(f"ProcesamientoLote creado: ID={procesamiento_lote.id}")
            
            # 6. Encolar tareas Celery para cada certificado
            logger.info("Encolando tareas Celery...")
            from ..tasks import generate_and_send_certificate_task
            
            for certificado in certificados_created:
                generate_and_send_certificate_task.delay(certificado.id)
            
            logger.info(f"{len(certificados_created)} tarea(s) Celery encolada(s)")
            
            # Actualizar estado del lote a 'processing'
            procesamiento_lote.estado = 'processing'
            procesamiento_lote.save()
            
            logger.info(f"Procesamiento masivo iniciado exitosamente. Lote ID: {procesamiento_lote.id}")
            return procesamiento_lote
            
        except Exception as e:
            logger.error(f"Error en procesamiento masivo: {str(e)}", exc_info=True)
            raise
