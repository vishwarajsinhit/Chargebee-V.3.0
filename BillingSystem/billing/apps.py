from django.apps import AppConfig


class BillingConfig(AppConfig):
    """Configuration class for the Billing application."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'BillingSystem.billing'

    def ready(self):
        import BillingSystem.billing.signals
