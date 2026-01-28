"""
Vistas para gestión de catálogos (Modalidad, Tipo, TipoEvento).
"""

from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Modalidad, Tipo, TipoEvento
from ..forms.catalogo_forms import ModalidadForm, TipoForm, TipoEventoForm

# Mixin para contexto común
class CatalogoContextMixin:
    titulo = ""
    breadcrumb_name = ""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.core.services.menu_service import MenuService
            context['menu_items'] = MenuService.get_menu_items(self.request.path, self.request.user)
        except ImportError:
            context['menu_items'] = []
            
        context['page_title'] = self.titulo
        return context

class AjaxFormMixin:
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'redirect_url': self.success_url
            })
        return response

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'html': self.render_to_response(self.get_context_data(form=form)).rendered_content
            }, safe=False)
            # Nota: El frontend espera HTML directo si falla, o podemos enviar JSON.
            # Según user_list.html: "else if (typeof data === 'string')" espera HTML.
            # Ajustaremos para retornar el HTML renderizado directamente si es error.
        
        return super().form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        # Override dispatch to handle form_invalid return for AJAX if needed in a specific way
        # For now relying on form_invalid is enough.
        # But wait, user_list.html JS handling:
        # .then(data => { if (typeof data === 'string') ... })
        # So for errors we should return HTML with status 400 maybe? Or just 200 with HTML string.
        return super().dispatch(request, *args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest' and hasattr(self, 'ajax_template_name'):
            self.template_name = self.ajax_template_name
        return super().render_to_response(context, **response_kwargs)



# ==================== MODALIDAD ====================

class ModalidadListView(LoginRequiredMixin, CatalogoContextMixin, ListView):
    model = Modalidad
    template_name = 'certificado/modalidad/modalidad_list.html'
    context_object_name = 'items'
    paginate_by = 10
    titulo = "Gestión de Modalidades"
    breadcrumb_name = "Modalidades"

    def get_queryset(self):
        return Modalidad.objects.all().order_by('nombre')

class ModalidadCreateView(LoginRequiredMixin, CatalogoContextMixin, AjaxFormMixin, CreateView):
    model = Modalidad
    form_class = ModalidadForm
    template_name = 'certificado/modalidad/modalidad_form.html'
    ajax_template_name = 'certificado/modalidad/modalidad_form_fields.html'
    success_url = reverse_lazy('certificado:modalidad_list')
    titulo = "Crear Modalidad"

    def form_valid(self, form):
        messages.success(self.request, f'Modalidad "{form.instance.nombre}" creada.')
        return super().form_valid(form)

class ModalidadUpdateView(LoginRequiredMixin, CatalogoContextMixin, AjaxFormMixin, UpdateView):
    model = Modalidad
    form_class = ModalidadForm
    template_name = 'certificado/modalidad/modalidad_form.html'
    ajax_template_name = 'certificado/modalidad/modalidad_form_fields.html'
    success_url = reverse_lazy('certificado:modalidad_list')
    titulo = "Editar Modalidad"

    def form_valid(self, form):
        messages.success(self.request, f'Modalidad "{form.instance.nombre}" actualizada.')
        return super().form_valid(form)

class ModalidadDeleteView(LoginRequiredMixin, CatalogoContextMixin, DeleteView):
    model = Modalidad
    template_name = 'certificado/modalidad/modalidad_confirm_delete.html'
    success_url = reverse_lazy('certificado:modalidad_list')
    titulo = "Eliminar Modalidad"

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Modalidad eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)

class ModalidadToggleActiveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        instance = get_object_or_404(Modalidad, pk=pk)
        instance.activo = not instance.activo
        instance.save()
        return JsonResponse({'success': True, 'is_active': instance.activo, 'message': 'Estado actualizado.'})

# ==================== TIPO ====================

class TipoListView(LoginRequiredMixin, CatalogoContextMixin, ListView):
    model = Tipo
    template_name = 'certificado/tipo/tipo_list.html'
    context_object_name = 'items'
    paginate_by = 10
    titulo = "Gestión de Tipos Generales"

    def get_queryset(self):
        return Tipo.objects.all().order_by('nombre')

class TipoCreateView(LoginRequiredMixin, CatalogoContextMixin, AjaxFormMixin, CreateView):
    model = Tipo
    form_class = TipoForm
    template_name = 'certificado/tipo/tipo_form.html'
    ajax_template_name = 'certificado/tipo/tipo_form_fields.html'
    success_url = reverse_lazy('certificado:tipo_list')
    titulo = "Crear Tipo General"

    def form_valid(self, form):
        messages.success(self.request, f'Tipo "{form.instance.nombre}" creado.')
        return super().form_valid(form)

class TipoUpdateView(LoginRequiredMixin, CatalogoContextMixin, AjaxFormMixin, UpdateView):
    model = Tipo
    form_class = TipoForm
    template_name = 'certificado/tipo/tipo_form.html'
    ajax_template_name = 'certificado/tipo/tipo_form_fields.html'
    success_url = reverse_lazy('certificado:tipo_list')
    titulo = "Editar Tipo General"

    def form_valid(self, form):
        messages.success(self.request, f'Tipo "{form.instance.nombre}" actualizado.')
        return super().form_valid(form)

class TipoDeleteView(LoginRequiredMixin, CatalogoContextMixin, DeleteView):
    model = Tipo
    template_name = 'certificado/tipo/tipo_confirm_delete.html'
    success_url = reverse_lazy('certificado:tipo_list')
    titulo = "Eliminar Tipo General"

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Tipo eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)

class TipoToggleActiveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        instance = get_object_or_404(Tipo, pk=pk)
        instance.activo = not instance.activo
        instance.save()
        return JsonResponse({'success': True, 'is_active': instance.activo, 'message': 'Estado actualizado.'})

# ==================== TIPO EVENTO ====================

class TipoEventoListView(LoginRequiredMixin, CatalogoContextMixin, ListView):
    model = TipoEvento
    template_name = 'certificado/tipo_evento/tipo_evento_list.html'
    context_object_name = 'items'
    paginate_by = 10
    titulo = "Gestión de Tipos de Evento"

    def get_queryset(self):
        return TipoEvento.objects.all().order_by('nombre')

class TipoEventoCreateView(LoginRequiredMixin, CatalogoContextMixin, AjaxFormMixin, CreateView):
    model = TipoEvento
    form_class = TipoEventoForm
    template_name = 'certificado/tipo_evento/tipo_evento_form.html'
    ajax_template_name = 'certificado/tipo_evento/tipo_evento_form_fields.html'
    success_url = reverse_lazy('certificado:tipo_evento_list')
    titulo = "Crear Tipo de Evento"

    def form_valid(self, form):
        messages.success(self.request, f'Tipo de Evento "{form.instance.nombre}" creado.')
        return super().form_valid(form)

class TipoEventoUpdateView(LoginRequiredMixin, CatalogoContextMixin, AjaxFormMixin, UpdateView):
    model = TipoEvento
    form_class = TipoEventoForm
    template_name = 'certificado/tipo_evento/tipo_evento_form.html'
    ajax_template_name = 'certificado/tipo_evento/tipo_evento_form_fields.html'
    success_url = reverse_lazy('certificado:tipo_evento_list')
    titulo = "Editar Tipo de Evento"

    def form_valid(self, form):
        messages.success(self.request, f'Tipo de Evento "{form.instance.nombre}" actualizado.')
        return super().form_valid(form)

class TipoEventoDeleteView(LoginRequiredMixin, CatalogoContextMixin, DeleteView):
    model = TipoEvento
    template_name = 'certificado/tipo_evento/tipo_evento_confirm_delete.html'
    success_url = reverse_lazy('certificado:tipo_evento_list')
    titulo = "Eliminar Tipo de Evento"

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Tipo de Evento eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)

class TipoEventoToggleActiveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        instance = get_object_or_404(TipoEvento, pk=pk)
        instance.activo = not instance.activo
        instance.save()
        return JsonResponse({'success': True, 'is_active': instance.activo, 'message': 'Estado actualizado.'})
