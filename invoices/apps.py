from django.apps import AppConfig


class InvoicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'invoices'
    verbose_name = 'Invoice Processing'

    def ready(self):
        from . import signals  # noqa: F401
