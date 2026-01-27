"""
Tareas Celery para generación y envío de certificados.

Este módulo define todas las tareas asíncronas del sistema.
"""

import os
import logging
from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone


logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_and_send_certificate_task(self, certificado_id: int):
    """
    Tarea principal: Genera DOCX, convierte a PDF y encola envío de email.
    
    Args:
        certificado_id: ID del certificado a generar
    
    Flujo:
        1. Cambiar estado a 'generating'
        2. Cargar datos de BD
        3. Obtener plantilla
        4. Construir variables
        5. Generar DOCX
        6. Convertir a PDF
        7. Guardar archivos
        8. Actualizar estado a 'completed'
        9. Encolar tarea de envío de email
    
    Retry:
        - Max 3 intentos
        - Delay: 60s, 120s, 300s (exponencial)
        - Solo en errores recuperables
    """
    from .models import Certificado
    from .services import TemplateService, PDFConversionService, CertificateStorageService
    from .utils import get_template_path
    
    certificado = None
    
    try:
        # Cargar certificado
        certificado = Certificado.objects.select_related(
            'evento', 'estudiante', 'evento__direccion'
        ).get(id=certificado_id)
        
        logger.info(f"[Certificado {certificado_id}] Iniciando generación para {certificado.estudiante.nombres_completos}")
        
        # Actualizar estado
        certificado.estado = 'generating'
        certificado.save(update_fields=['estado', 'updated_at'])
        
        # Obtener plantilla
        template_path = get_template_path(certificado.evento)
        logger.info(f"[Certificado {certificado_id}] Plantilla seleccionada: {template_path}")
        
        # Construir variables
        variables = TemplateService.get_variables_from_evento_estudiante(
            certificado.evento,
            certificado.estudiante
        )
        
        # Generar paths temporales
        temp_docx = CertificateStorageService.get_temp_path(
            f'cert_{certificado_id}_{certificado.estudiante.id}.docx'
        )
        
        # Generar DOCX
        logger.info(f"[Certificado {certificado_id}] Generando DOCX...")
        TemplateService.generate_docx(template_path, variables, temp_docx)
        
        # Convertir a PDF
        logger.info(f"[Certificado {certificado_id}] Convirtiendo a PDF...")
        temp_pdf = PDFConversionService.convert_docx_to_pdf(temp_docx)
        
        # Guardar archivos en ubicación final
        logger.info(f"[Certificado {certificado_id}] Guardando archivos...")
        docx_path, pdf_path = CertificateStorageService.save_certificate_files(
            evento_id=certificado.evento.id,
            estudiante_id=certificado.estudiante.id,
            docx_source_path=temp_docx,
            pdf_source_path=temp_pdf
        )
        
        # Actualizar certificado con rutas de archivos
        certificado.archivo_docx = docx_path
        certificado.archivo_pdf = pdf_path
        certificado.estado = 'completed'
        certificado.error_mensaje = ''
        certificado.save()
        
        logger.info(f"[Certificado {certificado_id}] Generación completada exitosamente")
        
        # Encolar tarea de envío de email
        send_certificate_email_task.delay(certificado_id)
        
        # Actualizar progreso del lote
        update_batch_progress_task.delay(certificado.evento.id)
        
        # Limpiar archivos temporales
        try:
            if os.path.exists(temp_docx):
                os.remove(temp_docx)
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)
        except:
            pass  # No es crítico
        
        return {
            'status': 'success',
            'certificado_id': certificado_id,
            'estudiante': certificado.estudiante.nombres_completos
        }
        
    except Exception as exc:
        logger.error(f"[Certificado {certificado_id}] Error: {str(exc)}", exc_info=True)
        
        # Actualizar certificado como fallido
        if certificado:
            certificado.estado = 'failed'
            certificado.error_mensaje = f"Error en generación: {str(exc)}"
            certificado.save()
            
            # Actualizar progreso del lote
            update_batch_progress_task.delay(certificado.evento.id)
        
        # Retry en errores recuperables
        if 'timeout' in str(exc).lower() or 'temporary' in str(exc).lower():
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        
        # No retry en otros errores
        return {
            'status': 'error',
            'certificado_id': certificado_id,
            'error': str(exc)
        }


@shared_task(bind=True, max_retries=5, rate_limit='30/m')
def send_certificate_email_task(self, certificado_id: int):
    """
    Tarea de envío de email con certificado PDF adjunto.
    
    Args:
        certificado_id: ID del certificado a enviar
    
    Rate limit:
        30 emails por minuto (configurado en decorator)
    
    Retry:
        - Max 5 intentos
        - Delay exponencial: 60s, 120s, 300s, 600s, 1200s
    """
    from .models import Certificado
    
    certificado = None
    
    try:
        # Cargar certificado
        certificado = Certificado.objects.select_related(
            'evento', 'estudiante'
        ).get(id=certificado_id)
        
        logger.info(f"[Email {certificado_id}] Enviando a {certificado.estudiante.correo_electronico}")
        
        # Verificar que existe el PDF
        if not certificado.archivo_pdf:
            raise ValueError("El certificado no tiene archivo PDF generado")
        
        # Actualizar estado
        certificado.estado = 'sending_email'
        certificado.save(update_fields=['estado', 'updated_at'])
        
        # Construir email
        subject = f"Certificado - {certificado.evento.nombre_evento}"
        body = f"""
Estimado/a {certificado.estudiante.nombres_completos},

Adjunto encontrará su certificado del evento:
{certificado.evento.nombre_evento}

Fecha: {certificado.evento.fecha_inicio.strftime('%d/%m/%Y')} - {certificado.evento.fecha_fin.strftime('%d/%m/%Y')}
Duración: {certificado.evento.duracion_horas} horas
Modalidad: {certificado.evento.get_modalidad_display()}

Saludos cordiales,
{certificado.evento.direccion.nombre}
        """.strip()
        
        # Crear email
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[certificado.estudiante.correo_electronico]
        )
        
        # Adjuntar PDF
        pdf_path = certificado.archivo_pdf.path if hasattr(certificado.archivo_pdf, 'path') else certificado.archivo_pdf
        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as pdf_file:
                email.attach(
                    filename=f'Certificado_{certificado.estudiante.nombres_completos.replace(" ", "_")}.pdf',
                    content=pdf_file.read(),
                    mimetype='application/pdf'
                )
        else:
            raise FileNotFoundError(f"Archivo PDF no encontrado: {pdf_path}")
        
        # Enviar email
        email.send(fail_silently=False)
        
        # Incrementar contador diario de emails
        from .models import DailyEmailLimit
        DailyEmailLimit.incrementar_contador(1)
        
        # Actualizar certificado
        certificado.estado = 'sent'
        certificado.enviado_email = True
        certificado.fecha_envio = timezone.now()
        certificado.intentos_envio += 1
        certificado.save()
        
        logger.info(f"[Email {certificado_id}] Enviado exitosamente")
        
        # Actualizar progreso del lote
        update_batch_progress_task.delay(certificado.evento.id)
        
        return {
            'status': 'success',
            'certificado_id': certificado_id,
            'email': certificado.estudiante.correo_electronico
        }
        
    except Exception as exc:
        logger.error(f"[Email {certificado_id}] Error: {str(exc)}", exc_info=True)
        
        # Actualizar intentos
        if certificado:
            certificado.intentos_envio += 1
            certificado.error_mensaje = f"Error en envío de email: {str(exc)}"
            certificado.save()
        
        # Retry
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        else:
            # Max retries alcanzado, marcar como fallido
            if certificado:
                certificado.estado = 'failed'
                certificado.save()
                update_batch_progress_task.delay(certificado.evento.id)
            
            return {
                'status': 'error',
                'certificado_id': certificado_id,
                'error': f"Max retries alcanzado: {str(exc)}"
            }


@shared_task
def update_batch_progress_task(evento_id: int):
    """
    Actualiza el progreso del procesamiento en lote.
    
    Args:
        evento_id: ID del evento
    
    Esta tarea se llama después de cada certificado procesado
    para actualizar los contadores del ProcesamientoLote.
    """
    from .models import ProcesamientoLote
    
    try:
        lote = ProcesamientoLote.objects.get(evento_id=evento_id)
        lote.actualizar_contadores()
        
        logger.info(
            f"[Lote {lote.id}] Progreso actualizado: "
            f"{lote.procesados}/{lote.total_estudiantes} "
            f"({lote.porcentaje_progreso}%)"
        )
        
        return {
            'status': 'success',
            'lote_id': lote.id,
            'progreso': lote.porcentaje_progreso
        }
        
    except Exception as exc:
        logger.error(f"[Lote Evento {evento_id}] Error actualizando progreso: {str(exc)}")
        return {
            'status': 'error',
            'evento_id': evento_id,
            'error': str(exc)
        }
