# 🚀 Documentación de Optimizaciones - Generación de Certificados
**Fecha:** 28 de Enero, 2026
**Autor:** Antigravity (Google Deepmind)

Este documento detalla los cambios críticos implementados para optimizar la generación masiva de certificados, solucionar problemas de variables y mejorar la experiencia de usuario.

## 1. ⚡ Optimización de Velocidad (Paralelismo)

### Problema Anterior
La generación era secuencial y lenta (~50s por certificado) porque LibreOffice usa un archivo de bloqueo (`lock file`) que impide ejecutar múltiples conversiones simultáneamente con el mismo perfil de usuario.

### Solución Implementada
Se modificó `PDFConversionService` para habilitar **paralelismo real**:
- **Perfiles Temporales Únicos:** Cada tarea de conversión crea ahora un directorio temporal de perfil de usuario (`-env:UserInstallation=file:///...`).
- **Resultado:** Múltiples workers de Celery pueden invocar LibreOffice al mismo tiempo sin bloquearse entre sí.
- **Archivo:** `apps/certificado/services/pdf_conversion_service.py`

### Instrucciones para Desarrollo Futuro
- Si se necesita más velocidad, **aumentar el número de workers de Celery** (`--concurrency=4` o más) en el script de arranque. El código ya soporta N conversiones simultáneas.

## 2. 📝 Corrección de Variables en Plantillas

### Problema Anterior
Variables con espacios (ej. `{{TIPO DE EVENTO}}`, `{{FECHA DE EMISION}}`) no eran reconocidas por la expresión regular y no se reemplazaban en el Word.

### Solución Implementada
- **Regex Actualizada:** Se modificó el patrón para aceptar espacios: `r'\{\{([A-Z_ ]+)\}\}'`.
- **Archivo:** `apps/certificado/utils/variable_replacer.py`

## 3. 💾 Eliminación de Archivos Temporales (Storage)

### Problema Anterior
Se guardaba el archivo `.docx` intermedio Y el `.pdf` final, duplicando espacio y tiempo de I/O innecesariamente.

### Solución Implementada
- **Solo PDF:** Ahora se genera el DOCX en `/tmp`, se convierte a PDF, y **solo se guarda el PDF** en la carpeta media final. El DOCX temporal se descarta.
- **Nuevo Método:** `CertificateStorageService.save_pdf_only`
- **Archivo:** `apps/certificado/tasks.py` y `apps/certificado/services/storage_service.py`

## 4. 🎨 UX - Loading Overlay Unificado

### Problema Anterior
Había indicadores de carga duplicados ("spinner" en botón + barra de progreso inline) y la interfaz permitía interacción durante la generación.

### Solución Implementada
- **Loading Overlay Premium:** Un overlay semitransparente bloquea toda la pantalla durante la generación.
- **Persistencia:** Si el usuario recarga la página mientras hay un lote procesando, el overlay **reaparece automáticamente** gracias a la lógica en `evento_detail.js`.
- **Archivos:** `static/js/certificado/loading_overlay.js` y `static/js/certificado/evento_detail.js`.

---

## 📂 Resumen de Archivos Modificados

| Archivo | Cambio Principal |
|---------|------------------|
| `apps/certificado/services/pdf_conversion_service.py` | Implementación de `UserInstallation` dinámico para paralelismo. |
| `apps/certificado/utils/variable_replacer.py` | Fix regex para variables con espacios. |
| `apps/certificado/tasks.py` | Flujo modificado para usar `save_pdf_only` y no guardar DOCX. |
| `apps/certificado/services/storage_service.py` | Nuevo método `save_pdf_only`. |
| `static/js/certificado/evento_detail.js` | Lógica de polling persistente y manejo de overlay. |
| `static/js/certificado/loading_overlay.js` | Componente visual del overlay. |

## ✅ Estado Actual
El sistema está listo para generar 200+ certificados de manera fluida. Las pruebas mostraron que las variables se reemplazan correctamente (incluso las que tienen espacios) y la velocidad ha mejorado gracias a la concurrencia.
