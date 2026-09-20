"""Seed the starter ServiceCity list for field engineers (idempotent).

Admins maintain the definitive list in Django admin; this just bootstraps common
cities (incl. the Kering store cities) so the multi-select is usable immediately.
Re-running is safe: existing cities are left untouched.
"""
from django.core.management.base import BaseCommand

from accounts.models import ServiceCity

CITIES = [
    ('Beijing', '北京'),
    ('Tianjin', '天津'),
    ('Shanghai', '上海'),
    ('Wuhan', '武汉'),
    ('Zhengzhou', '郑州'),
    ('Ningbo', '宁波'),
    ('Hangzhou', '杭州'),
    ('Chengdu', '成都'),
    ('Guangzhou', '广州'),
    ('Shenzhen', '深圳'),
]


class Command(BaseCommand):
    help = 'Seed the starter ServiceCity list for field engineers (idempotent).'

    def handle(self, *args, **options):
        created = 0
        for name_en, name_zh in CITIES:
            _city, was_created = ServiceCity.objects.get_or_create(
                name_en=name_en,
                defaults={'name_zh': name_zh},
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f'ServiceCity: {created} created, {ServiceCity.objects.count()} total.'
        ))
