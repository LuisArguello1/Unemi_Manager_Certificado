from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from ..forms.auth_forms import CustomAuthenticationForm

class CustomLoginView(LoginView):
    """
    Vista de Login personalizada.
    """
    template_name = 'accounts/login.html'
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Iniciar Sesión'
        return context

class CustomLogoutView(LogoutView):
    """
    Vista de Logout.
    """
    next_page = reverse_lazy('accounts:login')
