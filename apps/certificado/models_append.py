
class DailyEmailLimit(models.Model):
    """
    Modelo para trackear el límite diario de emails enviados.
    El límite se configura en settings.EMAIL_DAILY_LIMIT (default: 400).
    """
    fecha = models.DateField(unique=True, db_index=True, verbose_name="Fecha")
    emails_enviados = models.IntegerField(default=0, verbose_name="Emails Enviados")
    ultimo_reset = models.DateTimeField(auto_now=True, verbose_name="Último Reset")
    
    class Meta:
        verbose_name = "Límite Diario de Emails"
        verbose_name_plural = "Límites Diarios de Emails"
        ordering = ['-fecha']
    
    def __str__(self):
        from django.conf import settings
        limite = getattr(settings, 'EMAIL_DAILY_LIMIT', 400)
        return f"{self.fecha}: {self.emails_enviados}/{limite}"
    
    @classmethod
    def get_limite_diario(cls):
        """Obtiene el límite diario desde settings"""
        from django.conf import settings
        return getattr(settings, 'EMAIL_DAILY_LIMIT', 400)
    
    @classmethod
    def puede_enviar_email(cls):
        """
        Verifica si se puede enviar un email hoy.
        Returns:
            tuple: (puede_enviar: bool, emails_restantes: int)
        """
        hoy = timezone.now().date()
        limite_obj, created = cls.objects.get_or_create(
            fecha=hoy,
            defaults={'emails_enviados': 0}
        )
        
        limite_diario = cls.get_limite_diario()
        emails_restantes = limite_diario - limite_obj.emails_enviados
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
        limite_diario = cls.get_limite_diario()
        
        if cantidad > restantes:
            mensaje = (
                f"No se puede enviar el lote. Se requieren {cantidad} emails "
                f"pero solo quedan {restantes} disponibles hoy (límite: {limite_diario}/día)."
            )
            return False, restantes, mensaje
        
        return True, restantes, f"Se pueden enviar {cantidad} emails. Quedarán {restantes - cantidad} disponibles."
    
    @classmethod
    def incrementar_contador(cls, cantidad=1):
        """
        Incrementa el contador de emails enviados.
        
        Args:
            cantidad: Número de emails enviados (default: 1)
        """
        hoy = timezone.now().date()
        limite_obj, created = cls.objects.get_or_create(
            fecha=hoy,
            defaults={'emails_enviados': 0}
        )
        
        limite_obj.emails_enviados += cantidad
        limite_obj.save()
        
        return limite_obj.emails_enviados
