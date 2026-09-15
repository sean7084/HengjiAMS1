"""App configuration for the inspections app."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class InspectionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inspections'
    verbose_name = _('Store Inspections')
