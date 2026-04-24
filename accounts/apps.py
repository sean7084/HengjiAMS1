import os
import sys

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        if len(sys.argv) > 1 and sys.argv[1] != 'runserver':
            return
        if os.environ.get('RUN_MAIN') != 'true':
            return
        from .mailbox_sync import start_mailbox_sync_thread

        start_mailbox_sync_thread()
