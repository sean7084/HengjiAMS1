"""
Import the Kering master dataset into HengjiAMS.

Thin CLI wrapper around :func:`inspections.services.kering_import.import_kering_master`.
The heavy lifting (parsing, get-or-create logic, rollback tracking) lives in the
service so the web UI can drive the same flow from uploaded files.

Usage:
  python manage.py import_kering_master --schedule schedule.xlsx --assets asset_list_CN_2026.xlsx
  python manage.py import_kering_master --schedule ... --assets ... --dry-run
"""
import os

from django.core.management.base import BaseCommand, CommandError

from inspections.services.kering_import import import_kering_master


class Command(BaseCommand):
    help = 'Import the Kering schedule + master asset list into HengjiAMS (store inspections).'

    def add_arguments(self, parser):
        parser.add_argument('--schedule', required=True, help='Path to schedule.xlsx')
        parser.add_argument('--assets', required=True, help='Path to asset_list_CN_2026.xlsx')
        parser.add_argument('--company-name', default='Kering', help='Client company name (default: Kering)')
        parser.add_argument('--company-code', default='KER', help='Client company code (default: KER)')
        parser.add_argument('--engineer', default=None, help='Optional username to assign as onsite engineer')
        parser.add_argument('--dry-run', action='store_true', help='Preview without persisting changes')
        parser.add_argument('--no-track-rollback', action='store_true',
                            help='Skip ImportRun rollback tracking (faster for very large imports)')

    def handle(self, *args, **options):
        schedule_path = options['schedule']
        assets_path = options['assets']
        for path in (schedule_path, assets_path):
            if not os.path.exists(path):
                raise CommandError(f'File not found: {path}')

        engineer = None
        if options['engineer']:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            engineer = User.objects.filter(username=options['engineer']).first()
            if engineer is None:
                raise CommandError(f'Engineer user not found: {options["engineer"]}')

        result = import_kering_master(
            schedule_path,
            assets_path,
            company_name=options['company_name'],
            company_code=options['company_code'],
            engineer=engineer,
            batch=None,
            user=None,
            dry_run=options['dry_run'],
            track_rollback=not options['no_track_rollback'],
        )

        stats = result['stats']
        per_store = result['per_store']

        prefix = '[DRY RUN] ' if options['dry_run'] else ''
        self.stdout.write(f'{prefix}Import complete:')
        for key in ('companies', 'divisions', 'locations', 'inspections',
                    'categories', 'brands', 'models', 'assets', 'devices'):
            self.stdout.write(f'  {key}: {stats[key]}')
        if stats['devices_skipped_duplicate']:
            self.stdout.write(f'  devices_skipped_duplicate: {stats["devices_skipped_duplicate"]}')
        if per_store:
            self.stdout.write(f'{prefix}Per-store summary:')
            for jda in sorted(per_store):
                entry = per_store[jda]
                self.stdout.write(f'  {jda} {entry["store"]}: {entry["devices"]} devices')
