"""Group store inspections that have no batch into planning cycles.

Imports run from the CLI (``import_kering_master``) attach no batch, so those
inspections are listed on the dashboard / review pages but can never appear on
``/inspections/batches/`` - which only ever shows ``InspectionBatch`` rows. This
command adopts them, either into one named batch or into one batch per company
per calendar month named ``<Company> <YYYY-MM>``, with the date range tightened
to the inspections it contains.

Idempotent: batches are looked up by (company, name), so re-running only adopts
inspections that are still unassigned and widens the existing range.

Usage:
  python manage.py group_unbatched_inspections --dry-run
  python manage.py group_unbatched_inspections --name "2026 Kering Gucci & YSL"
  python manage.py group_unbatched_inspections --by week --company KER
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from companies.models import Company
from inspections.models import InspectionBatch, StoreInspection


class Command(BaseCommand):
    help = ('Group inspections that have no batch into one named batch, or into '
            'per-company monthly (or weekly) batches.')

    def add_arguments(self, parser):
        parser.add_argument('--by', choices=('month', 'week'), default=None,
                            help='Grouping period when --name is not given (default: month)')
        parser.add_argument('--name', default=None,
                            help='Put every matched inspection into ONE batch with this name '
                                 '(ignores --by; all matched inspections must share a company)')
        parser.add_argument('--company', default=None,
                            help='Only adopt inspections of this company code (e.g. KER)')
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would happen without writing anything')

    def _period_label(self, day, period):
        if period == 'week':
            iso = day.isocalendar()
            return f'{iso[0]}-W{iso[1]:02d}'
        return day.strftime('%Y-%m')

    def handle(self, *args, **options):
        single_name = (options['name'] or '').strip()
        period = options['by'] or 'month'
        dry_run = options['dry_run']

        orphaned = StoreInspection.objects.filter(batch__isnull=True).select_related(
            'company', 'division'
        ).order_by('inspection_date')
        if options['company']:
            company = Company.objects.filter(code__iexact=options['company'].strip()).first()
            if company is None:
                raise CommandError(f'Company not found: {options["company"]}')
            orphaned = orphaned.filter(company=company)

        groups = {}
        skipped = 0
        for inspection in orphaned:
            if inspection.company_id is None or inspection.inspection_date is None:
                skipped += 1
                continue
            if single_name:
                label = single_name
            else:
                label = self._period_label(inspection.inspection_date, period)
            key = (inspection.company_id, label)
            groups.setdefault(key, []).append(inspection)

        if single_name and len({company_id for company_id, _label in groups}) > 1:
            raise CommandError(
                'The unbatched inspections span several companies, so a single named batch is '
                'ambiguous; pass --company <code> to pick one, or drop --name to group by period.'
            )

        if not groups:
            self.stdout.write('No unbatched inspections to adopt.')
            if skipped:
                self.stderr.write(f'  ({skipped} row(s) skipped: no company or no inspection date)')
            return

        total = sum(len(rows) for rows in groups.values())
        prefix = '[DRY RUN] ' if dry_run else ''
        self.stdout.write(f'{prefix}Adopting {total} inspection(s) into {len(groups)} batch(es):')

        with transaction.atomic():
            for company_id, label in sorted(groups, key=lambda key: (key[1], key[0])):
                inspections = groups[(company_id, label)]
                company = inspections[0].company
                dates = [row.inspection_date for row in inspections]
                start, end = min(dates), max(dates)
                name = label if single_name else f'{company.name} {label}'

                # Only pin a brand when the group is unambiguous; a mixed
                # Gucci + YSL cycle is better left without one than mislabelled.
                division_ids = {row.division_id for row in inspections if row.division_id}
                division_id = division_ids.pop() if len(division_ids) == 1 else None

                batch, created = InspectionBatch.objects.get_or_create(
                    company=company,
                    name=name,
                    defaults={
                        'start_date': start,
                        'end_date': end,
                        'source': InspectionBatch.Source.MANUAL,
                        'division_id': division_id,
                        'description': (
                            f'Adopted {len(inspections)} previously unbatched inspection(s) '
                            f'with group_unbatched_inspections.'
                        ),
                    },
                )
                if not created:
                    # Widen an existing cycle to cover the newly adopted rows.
                    batch.start_date = min(batch.start_date, start)
                    batch.end_date = max(batch.end_date, end)
                    batch.save(update_fields=['start_date', 'end_date', 'updated_at'])

                StoreInspection.objects.filter(
                    id__in=[row.id for row in inspections]
                ).update(batch=batch, updated_at=timezone.now())

                self.stdout.write(
                    f'  {"created" if created else "reused "} {name}: '
                    f'{len(inspections)} inspection(s), {start} .. {end}'
                )

            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write('[DRY RUN] no changes were written.')

        if skipped:
            self.stderr.write(f'  ({skipped} row(s) skipped: no company or no inspection date)')
