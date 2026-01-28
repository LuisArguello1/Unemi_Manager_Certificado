"""
Modelo para trackear límite diario de envío de emails.
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta


from django.conf import settings

class DailyEmailLimit(models.Model):
    """
    Modelo para trackear el límite díario de emails enviados.
    Límite: Configurado en settings (EMAIL_DAILY_LIMIT).
    """
    fecha = models.DateField(unique=True, db_index=True)
    emails_enviados = models.IntegerField(default=0)
    ultimo_reset = models.DateTimeField(auto_now=True)
    
    @property
    def LIMITE_DIARIO(self):
        return getattr(settings, 'EMAIL_DAILY_LIMIT', 400)
    
    @classmethod
    def get_limit(cls):
        return getattr(settings, 'EMAIL_DAILY_LIMIT', 400)

    class Meta:
        verbose_name = "Límite Diario de Emails"
        verbose_name_plural = "Límites Diarios de Emails"
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.fecha}: {self.emails_enviados}/{self.get_limit()}"
    
    @classmethod
    def puede_enviar_email(cls):
        """
        Verifica si se puede enviar un email hoy.
        Returns:
            tuple: (puede_enviar: bool, emails_restantes: int)
        """
        hoy = timezone.now().date()
        limite, created = cls.objects.get_or_create(
            fecha=hoy,
            defaults={'emails_enviados': 0}
        )
        
        emails_restantes = cls.get_limit() - limite.emails_enviados
        puede_enviar = emails_restantes > 0
        
        return puede_enviar, emails_restantes
    
    @classmethod
    def puede_enviar_lote(cls, cantidad):
        """
        Verifica si se puede enviar un lote de emails.
        
        Args:
            cantidad: Número de emails a enviar
        
        Returns:
            tuple: (puede_enviar: bool, emails_restantes: int, mensaje: str)
        """
        puede, restantes = cls.puede_enviar_email()
        
        if cantidad > restantes:
            mensaje = (
                f"No se puede enviar el lote. Se requieren {cantidad} emails "
                f"pero solo quedan {restantes} disponibles hoy (límite: {cls.get_limit()}/día)."
            )
            return False, restantes, mensaje
        
        return True, restantes, f"Se pueden enviar {cantidad} emails. Restantes: {restantes - cantidad}"
    
    @classmethod
    def incrementar_contador(cls, cantidad=1):
        """
        Incrementa el contador de emails enviados.
        
        Args:
            cantidad: Número de emails enviados (default: 1)
        """
        hoy = timezone.now().date()
        limite, created = cls.objects.get_or_create(
            fecha=hoy,
            defaults={'emails_enviados': 0}
        )
        
        limite.emails_enviados += cantidad
        limite.save()
        
        return limite.emails_enviados
    
    @classmethod
    def limpiar_registros_antiguos(cls, dias=30):
        """
        Limpia registros más antiguos que X días.
        
        Args:
            dias: Días a mantener (default: 30)
        """
        fecha_limite = timezone.now().date() - timedelta(days=dias)
        cls.objects.filter(fecha__lt=fecha_limite).delete()
