"""
WSGI config for hengjiams project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from hengjiams.runtime_setup import configure_windows_fontconfig, load_local_env

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hengjiams.settings')
load_local_env()
configure_windows_fontconfig()

application = get_wsgi_application()
