from django import forms
from django.contrib.auth.forms import AuthenticationForm
from apps.core.forms.base_form import BaseFormMixin

class CustomAuthenticationForm(BaseFormMixin, AuthenticationForm):
    """
    Formulario de login personalizado con estilos Tailwind.
    """
    # BaseFormMixin se encargará de los estilos
    pass
