"""
Vistas para el sistema de certificados.
"""

from django.views.generic import TemplateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from ..models import ProcesamientoLote, Certificado, VariantePlantilla
from ..forms import EventoForm, ExcelUploadForm
from ..services import CertificadoService
import logging


logger = logging.getLogger(__name__)


class CertificadoCreateView(LoginRequiredMixin, TemplateView):
    """
    Vista para crear evento y generar certificados masivamente.
    """
    template_name = 'certificado/certificado_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evento_form'] = EventoForm()
        context['excel_form'] = ExcelUploadForm()
        return context
    
    def post(self, request, *args, **kwargs):
        """
        Procesa el formulario y genera certificados.
        """
        evento_form = EventoForm(request.POST)
        excel_form = ExcelUploadForm(request.POST, request.FILES)
        
        if evento_form.is_valid() and excel_form.is_valid():
            try:
                # Procesar generación masiva
                lote = CertificadoService.process_bulk_certificates(
                    evento_data=evento_form.cleaned_data,
                    excel_file=request.FILES['archivo_excel'],
                    user=request.user
                )
                
                messages.success(
                    request,
                    f'Procesamiento iniciado. {lote.total_estudiantes} certificado(s) en cola.'
                )
                
                # Redirigir a página de estado
                return redirect('certificado:procesamiento_status', pk=lote.id)
                
            except Exception as e:
                logger.error(f"Error al procesar certificados: {str(e)}", exc_info=True)
                messages.error(request, f'Error al procesar certificados: {str(e)}')
        
        else:
            # Mostrar errores de formulario
            for field, errors in evento_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            
            for field, errors in excel_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        
        # Volver al formulario con errores
        context = self.get_context_data()
        context['evento_form'] = evento_form
        context['excel_form'] = excel_form
        return self.render_to_response(context)


class ProcesamientoStatusView(LoginRequiredMixin, DetailView):
    """
    Vista de estado del procesamiento en lote.
    """
    model = ProcesamientoLote
    template_name = 'certificado/procesamiento_status.html'
    context_object_name = 'lote'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener todos los certificados del lote
        context['certificados'] = Certificado.objects.filter(
            evento=self.object.evento
        ).select_related('estudiante').order_by('estudiante__nombres_completos')
        
        return context


class CertificadoListView(LoginRequiredMixin, ListView):
    """
    Vista de lista de certificados generados.
    """
    model = Certificado
    template_name = 'certificado/certificado_list.html'
    context_object_name = 'certificados'
    paginate_by = 50
    
    def get_queryset(self):
        qs = super().get_queryset().select_related(
            'evento', 'estudiante', 'evento__direccion'
        ).order_by('-created_at')
        
        # Filtros opcionales
        evento_id = self.request.GET.get('evento')
        estado = self.request.GET.get('estado')
        
        if evento_id:
            qs = qs.filter(evento_id=evento_id)
        
        if estado:
            qs = qs.filter(estado=estado)
        
        return qs


def get_variantes_api(request, direccion_id):
    """
    API endpoint para obtener variantes de plantilla por dirección.
    Usado por AJAX en el formulario.
    
    Args:
        request: HttpRequest
        direccion_id: ID de la dirección
    
    Returns:
        JsonResponse con variantes disponibles
    """
    try:
        variantes = VariantePlantilla.objects.filter(
            plantilla_base__direccion_id=direccion_id,
            plantilla_base__es_activa=True,
            activo=True
        ).select_related('plantilla_base').order_by('orden', 'nombre')
        
        variantes_data = [
            {
                'id': v.id,
                'nombre': v.nombre,
                'descripcion': v.descripcion
            }
            for v in variantes
        ]
        
        return JsonResponse({
            'success': True,
            'variantes': variantes_data
        })
        
    except Exception as e:
        logger.error(f"Error al obtener variantes: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
