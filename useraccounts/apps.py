from django.apps import AppConfig


class UseraccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'useraccounts'
    verbose_name = 'User Accounts'
    
    def ready(self):
        """
        Import signals when the app is ready
        """
        import useraccounts.signals
