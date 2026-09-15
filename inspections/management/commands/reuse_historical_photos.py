"""
Reuse historical photos for planned store inspections.

DB-native port of the EUS historical-photo step: for a target inspection (or all
planned inspections for a store/date), copy reusable overall/serial photos from the
most recent prior inspection of the same store, matched by serial number, and mark
matched devices photo_required=False so engineers do not re-shoot them onsite.

Usage:
  python manage.py reuse_historical_photos --inspection <uuid>
  python manage.py reuse_historical_photos --jda 22149 --date 2026-09-02
  python manage.py reuse_historical_photos --all-planned
"""
from django.core.management.base import BaseCommand, CommandError

from inspections.models import StoreInspection
from inspections.services.historical_photos import reuse_historical_photos


class Command(BaseCommand):
    help = 'Copy reusable photos from prior inspections into planned store inspections.'

    def add_arguments(self, parser):
        parser.add_argument('--inspection', default=None, help='Target StoreInspection UUID')
        parser.add_argument('--jda', default=None, help='Filter planned inspections by JDA code')
        parser.add_argument('--date', default=None, help='Filter planned inspections by inspection_date (YYYY-MM-DD)')
        parser.add_argument('--all-planned', action='store_true', help='Process every planned inspection')

    def handle(self, *args, **options):
        targets = self._resolve_targets(options)
        if not targets:
            raise CommandError('No target inspections matched.')

        total_devices = 0
        total_photos = 0
        for inspection in targets:
            result = reuse_historical_photos(inspection)
            total_devices += result['devices_matched']
            total_photos += result['photos_copied']
            self.stdout.write(
                f'{inspection.store_label or inspection.id}: '
                f"{result['devices_matched']} devices, {result['photos_copied']} photos "
                f"(source: {result['source_inspection'] or 'none'})"
            )
        self.stdout.write(self.style.SUCCESS(
            f'Done. {total_devices} devices matched, {total_photos} photos copied.'
        ))

    def _resolve_targets(self, options):
        if options['inspection']:
            inspection = StoreInspection.objects.filter(pk=options['inspection']).first()
            return [inspection] if inspection else []

        queryset = StoreInspection.objects.filter(status=StoreInspection.Status.PLANNED)
        if not options['all_planned'] and not options['jda'] and not options['date']:
            return []
        if options['jda']:
            queryset = queryset.filter(jda_code=options['jda'])
        if options['date']:
            queryset = queryset.filter(inspection_date=options['date'])
        return list(queryset)
