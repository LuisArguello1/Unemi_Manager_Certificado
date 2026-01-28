"""
Servicio para convertir documentos DOCX a PDF usando LibreOffice.
"""

import os
import subprocess
import logging
from django.conf import settings


logger = logging.getLogger(__name__)


class PDFConversionError(Exception):
    """
    Error durante la conversión de DOCX a PDF.
    """
    pass


class PDFConversionService:
    """
    Servicio para convertir documentos DOCX a PDF usando LibreOffice headless.
    
    Requiere LibreOffice instalado en el sistema.
    """
    
    @staticmethod
    def convert_docx_to_pdf(docx_path: str, output_dir: str = None) -> str:
        """
        Convierte un archivo DOCX a PDF usando LibreOffice headless.
        
        Args:
            docx_path: Ruta absoluta al archivo .docx
            output_dir: Directorio donde guardar el PDF (si None, usa el mismo directorio que el DOCX)
        
        Returns:
            Ruta absoluta del archivo PDF generado
        
        Raises:
            PDFConversionError: Si la conversión falla
            FileNotFoundError: Si LibreOffice no está instalado o el DOCX no existe
        
        Ejemplo:
            >>> from apps.certificado.services.pdf_conversion_service import PDFConversionService
            >>> pdf_path = PDFConversionService.convert_docx_to_pdf('/path/to/certificado.docx')
            >>> print(pdf_path)  # /path/to/certificado.pdf
        """
        try:
            # Validar que existe el archivo DOCX
            if not os.path.exists(docx_path):
                raise FileNotFoundError(f"Archivo DOCX no encontrado: {docx_path}")
            
            # Determinar directorio de salida
            if output_dir is None:
                output_dir = os.path.dirname(docx_path)
            
            # Crear directorio si no existe
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # Obtener ruta de LibreOffice desde settings
            libreoffice_path = getattr(settings, 'LIBREOFFICE_PATH', 'soffice')
            
            # Configurar perfil de usuario único para paralelismo
            import uuid
            import shutil
            import tempfile
            from urllib.parse import quote
            
            # Crear directorio temporal único para esta instancia
            unique_id = str(uuid.uuid4())
            user_profile_dir = os.path.join(tempfile.gettempdir(), f"LO_{unique_id}")
            
            # Convertir a formato URL file:/// compatible con Windows/Linux
            # En Windows: C:\Users\...\Temp\LO_xyz -> file:///C:/Users/.../Temp/LO_xyz
            user_installation_url = f"file:///{user_profile_dir.replace(os.sep, '/')}"
            
            logger.info(f"Convirtiendo DOCX a PDF: {docx_path} (Perfil: {unique_id})")
            
            # Comando para LibreOffice headless con perfil personalizado
            command = [
                libreoffice_path,
                f"-env:UserInstallation={user_installation_url}",
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', output_dir,
                docx_path
            ]
            
            # Ejecutar comando
            try:
                logger.debug(f"Ejecutando comando: {' '.join(command)}")
                # Usar creación de ventana oculta en Windows para evitar popups
                startupwu = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=180,  # Timeout aumentado a 180 segundos
                    startupinfo=startupinfo if os.name == 'nt' else None
                )
                
                # Verificar si hubo error
                if result.returncode != 0:
                    error_msg = result.stderr or result.stdout
                    logger.error(f"Error en conversión LibreOffice: {error_msg}")
                    raise PDFConversionError(
                        f"LibreOffice retornó código {result.returncode}: {error_msg}"
                    )
                    
            finally:
                # Limpiar directorio de perfil temporal siempre
                if os.path.exists(user_profile_dir):
                    try:
                        shutil.rmtree(user_profile_dir, ignore_errors=True)
                    except Exception as e:
                        logger.warning(f"No se pudo limpiar directorio temporal {user_profile_dir}: {e}")
            
            # Construir ruta del PDF generado
            docx_filename = os.path.basename(docx_path)
            pdf_filename = os.path.splitext(docx_filename)[0] + '.pdf'
            pdf_path = os.path.join(output_dir, pdf_filename)
            
            # Validar que se generó el PDF
            if not os.path.exists(pdf_path):
                raise PDFConversionError(
                    f"El PDF no se generó correctamente. Esperado en: {pdf_path}"
                )
            
            logger.info(f"PDF generado exitosamente: {pdf_path}")
            return pdf_path
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout al convertir DOCX a PDF: {docx_path}")
            raise PDFConversionError(f"Timeout al convertir documento (>180s)")
        except Exception as e:
            logger.error(f"Error al convertir DOCX a PDF: {str(e)}")
            raise
    
    @staticmethod
    def verify_libreoffice_installed() -> bool:
        """
        Verifica si LibreOffice está instalado y accesible.
        
        Returns:
            True si LibreOffice está disponible, False en caso contrario
        """
        try:
            libreoffice_path = getattr(settings, 'LIBREOFFICE_PATH', 'soffice')
            
            result = subprocess.run(
                [libreoffice_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info(f"LibreOffice encontrado: {result.stdout.strip()}")
                return True
            else:
                logger.warning(f"LibreOffice no responde correctamente")
                return False
                
        except Exception as e:
            logger.warning(f"LibreOffice no disponible: {str(e)}")
            return False
