"""
Vistas para gestión de direcciones/gestiones institucionales.
"""

from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from ..models import Direccion
from ..forms.direccion_form import DireccionForm
from .catalogo_views import AjaxFormMixin
import logging

logger = logging.getLogger(__name__)


class DireccionListView(LoginRequiredMixin, ListView):
    """
    Vista de listado de direcciones con paginación.
    """
    model = Direccion
    template_name = 'certificado/direccion/direccion_list.html'
    context_object_name = 'direcciones'
    paginate_by = 12
    
    def get_queryset(self):
        """Ordenar por nombre"""
        return Direccion.objects.all().order_by('nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
        
        context['breadcrumbs'] = [{'name': 'Direcciones'}]
        context['page_title'] = 'Direcciones/Gestiones'
        return context


class DireccionDetailView(LoginRequiredMixin, DetailView):
    """
    Vista de detalle de una dirección mostrando sus plantillas asociadas.
    """
    model = Direccion
    template_name = 'certificado/direccion/direccion_detail.html'
    context_object_name = 'direccion'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
        
        context['breadcrumbs'] = [
            {'name': 'Direcciones', 'url': reverse('certificado:direccion_list')},
            {'name': self.object.nombre}
        ]
        context['page_title'] = f'Detalle: {self.object.nombre}'
        context['plantillas'] = self.object.plantillas_base.all().order_by('-created_at')
        return context


class DireccionCreateView(LoginRequiredMixin, AjaxFormMixin, CreateView):
    """
    Vista para crear nueva dirección.
    """
    model = Direccion
    form_class = DireccionForm
    template_name = 'certificado/direccion/direccion_form.html'
    ajax_template_name = 'certificado/direccion/direccion_form_fields.html'
    success_url = reverse_lazy('certificado:direccion_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
        
        context['breadcrumbs'] = [
            {'name': 'Direcciones', 'url': reverse('certificado:direccion_list')},
            {'name': 'Crear Dirección'}
        ]
        context['page_title'] = 'Crear Nueva Dirección/Gestión'
        return context
    
    def form_valid(self, form):
        """Mensaje de éxito"""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Dirección "{self.object.nombre}" creada exitosamente con código {self.object.codigo}.'
        )
        return response
    
    def form_invalid(self, form):
        """Mostrar errores"""
        messages.error(self.request, 'Por favor corrija los errores en el formulario.')
        return super().form_invalid(form)


class DireccionUpdateView(LoginRequiredMixin, AjaxFormMixin, UpdateView):
    """
    Vista para editar dirección.
    """
    model = Direccion
    form_class = DireccionForm
    template_name = 'certificado/direccion/direccion_form.html'
    ajax_template_name = 'certificado/direccion/direccion_form_fields.html'
    success_url = reverse_lazy('certificado:direccion_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
        
        context['breadcrumbs'] = [
            {'name': 'Direcciones', 'url': reverse('certificado:direccion_list')},
            {'name': 'Editar Dirección'}
        ]
        context['page_title'] = f'Editar: {self.object.nombre}'
        return context
    
    def form_valid(self, form):
        """Mensaje de éxito"""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Dirección "{self.object.nombre}" actualizada exitosamente.'
        )
        return response
    
    def form_invalid(self, form):
        """Mostrar errores"""
        messages.error(self.request, 'Por favor corrija los errores en el formulario.')
        return super().form_invalid(form)


class DireccionDeleteView(LoginRequiredMixin, DeleteView):
    """
    Vista para eliminar dirección.
    """
    model = Direccion
    template_name = 'certificado/direccion/direccion_confirm_delete.html'
    success_url = reverse_lazy('certificado:direccion_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
        
        context['breadcrumbs'] = [
            {'name': 'Direcciones', 'url': reverse('certificado:direccion_list')},
            {'name': 'Eliminar Dirección'}
        ]
        context['page_title'] = 'Eliminar Dirección'
        context['num_plantillas'] = self.object.plantillas_base.count()
        context['num_eventos'] = self.object.eventos.count()
        return context
    
    def delete(self, request, *args, **kwargs):
        """Override para mostrar mensaje de éxito"""
        direccion_nombre = self.get_object().nombre
        response = super().delete(request, *args, **kwargs)
        messages.success(
            self.request,
            f'Dirección "{direccion_nombre}" eliminada exitosamente.'
        )
        return response


class DireccionToggleActiveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Solicitud inválida'}, status=400)
        
        item = get_object_or_404(Direccion, pk=pk)
        item.activo = not item.activo
        item.save()
        
        return JsonResponse({
            'success': True,
            'is_active': item.activo,
            'message': f'Estado de "{item.nombre}" actualizado correctamente.'
        })
