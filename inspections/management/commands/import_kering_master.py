"""
Import the Kering master dataset into HengjiAMS.

Reads a schedule workbook (store visits) and a master asset workbook (per-store
device inventory) and creates/updates:
  companies.Company (Kering) -> companies.Division (brand) -> companies.Location (store)
  assets.AssetCategory / AssetBrand / AssetModel / Asset (device)
  inspections.StoreInspection (visit) + inspections.InspectionDevice (expected lines)

Kering-specific attributes that have no home on the generic Asset model
(Usage, 照片需求, 大纲, 注释, inspection-time status) are stored on InspectionDevice.

The whole run is wrapped in a transaction; with --dry-run it is rolled back after
reporting what would happen. Non-dry runs are tracked as an ImportRun (shared
rollback system) unless --no-track-rollback is passed. Device categories are
normalized and placeholder identifiers cleaned exactly like the legacy EUS pipeline.

Usage:
  python manage.py import_kering_master --schedule schedule.xlsx --assets asset_list_CN_2026.xlsx
  python manage.py import_kering_master --schedule ... --assets ... --dry-run
"""
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from assets.models import Asset, AssetBrand, AssetCategory, AssetModel
from companies.models import Company, Division, Location
from inspections.constants import (
    ASSET_PLACEHOLDER_PREFIX,
    PHOTO_NOT_REQUIRED_TAG,
    PHOTO_REQUIRED_TAG,
    is_placeholder_identifier,
    normalize_device_category,
)
from inspections.models import InspectionDevice, StoreInspection
from utils.import_rollback import finalize_import_run, record_import_change, start_import_run

SCHEDULE_COLUMNS = {
    'jda': ['JDA code', 'JDA', 'jda_code', 'jda'],
    'brand': ['Brand', 'brand', '品牌'],
    'store': ['Store Name', 'store_name', 'store', '店铺名称'],
    'date': ['inspection_date', 'date', 'Inspection Date', '日期'],
}
ASSET_COLUMNS = {
    'store': ['STORE', 'Store', 'store'],
    'jda': ['JDA', 'jda', 'JDA code'],
    'asset_id': ['Asset ID', 'asset_id', '资产编号'],
    'category': ['Category', 'category', '设备类型'],
    'brand_model': ['Brand-Model', 'brand_model', '设备型号'],
    'sn': ['SN', 'sn', '序列号'],
    'warranty_start': ['Warranty-start', 'warranty_start', 'Warranty Start'],
    'usage': ['Usage', 'usage'],
    'status': ['Status', 'status'],
    'photo_requirement': ['照片需求', 'photo_requirement', 'Photo Requirement'],
    'outline': ['大纲', 'outline'],
    'device_notes': ['注释', 'device_notes', 'notes'],
}


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

        schedule_rows = self._read_rows(schedule_path)
        asset_rows = self._read_rows(assets_path)

        stats = {
            'companies': 0, 'divisions': 0, 'locations': 0, 'inspections': 0,
            'categories': 0, 'brands': 0, 'models': 0, 'assets': 0, 'devices': 0,
            'devices_skipped_duplicate': 0,
        }
        created = {key: set() for key in stats}
        per_store = {}

        # Rollback tracking via the shared ImportRun system (skipped for dry runs
        # and when --no-track-rollback is passed).
        self._seq = 0
        self._run = None
        if not options['dry_run'] and not options['no_track_rollback']:
            self._run = start_import_run(None, 'inspections', 'kering_master', total_rows=len(asset_rows))

        with transaction.atomic():
            company, company_created = Company.objects.get_or_create(
                name=options['company_name'],
                defaults={'code': options['company_code'], 'status': Company.CompanyStatus.ACTIVE},
            )
            if company_created:
                stats['companies'] += 1
            self._record(company, company_created)

            # Pass 1: schedule -> divisions (brands), locations (stores), inspections.
            inspection_by_jda = {}
            for row in schedule_rows:
                jda = self._normalize_jda(self._get(row, SCHEDULE_COLUMNS['jda']))
                if not jda:
                    continue
                brand = self._clean(self._get(row, SCHEDULE_COLUMNS['brand']))
                store = self._clean(self._get(row, SCHEDULE_COLUMNS['store']))
                inspection_date = self._parse_date(self._get(row, SCHEDULE_COLUMNS['date']))

                division = None
                if brand:
                    division, div_created = Division.objects.get_or_create(
                        company=company, name=brand, defaults={'code': brand[:20]},
                    )
                    if div_created:
                        stats['divisions'] += 1
                    self._record(division, div_created)

                location, loc_created = Location.objects.get_or_create(
                    company=company, code=jda,
                    defaults={
                        'name': store or jda,
                        'division': division,
                        'location_type': Location.LocationType.STORE,
                    },
                )
                if loc_created:
                    stats['locations'] += 1
                self._record(location, loc_created)

                store_label = ' '.join(part for part in [jda, brand, store] if part).strip()
                if inspection_date is None:
                    self.stderr.write(self.style.WARNING(f'Schedule row for JDA {jda} has no valid date; skipping.'))
                    continue
                inspection, insp_created = StoreInspection.objects.get_or_create(
                    location=location, inspection_date=inspection_date,
                    defaults={
                        'company': company, 'division': division, 'jda_code': jda,
                        'brand_name': brand, 'store_name': store, 'store_label': store_label,
                        'engineer': engineer, 'status': StoreInspection.Status.PLANNED,
                    },
                )
                if insp_created:
                    stats['inspections'] += 1
                self._record(inspection, insp_created)
                inspection_by_jda[jda] = inspection
                per_store[jda] = {'store': store_label, 'devices': 0}

            # Pass 2: master asset list -> assets + expected inspection devices.
            placeholder_seq = 0
            for row in asset_rows:
                jda = self._normalize_jda(self._get(row, ASSET_COLUMNS['jda']))
                inspection = inspection_by_jda.get(jda)
                if inspection is None:
                    # No scheduled visit for this JDA; nothing to attach devices to.
                    continue

                category_raw = self._clean(self._get(row, ASSET_COLUMNS['category']))
                brand_model = self._clean(self._get(row, ASSET_COLUMNS['brand_model']))
                sn = self._clean_identifier(self._get(row, ASSET_COLUMNS['sn']))
                asset_id = self._clean_identifier(self._get(row, ASSET_COLUMNS['asset_id']))

                asset = self._ensure_asset(
                    company=company, inspection=inspection, category_raw=category_raw,
                    brand_model=brand_model, sn=sn, asset_id=asset_id,
                    warranty_start=self._parse_date(self._get(row, ASSET_COLUMNS['warranty_start'])),
                    stats=stats,
                )

                # Rows missing both Asset ID and SN get a stable placeholder SN
                # (like the EUS pipeline) so they stay distinct and re-importable.
                device_sn = sn
                if not device_sn and not asset_id:
                    placeholder_seq += 1
                    device_sn = f'{ASSET_PLACEHOLDER_PREFIX}-{placeholder_seq:06d}'

                uid = f'{jda}:{asset_id or device_sn or asset.asset_number}'
                if uid in created['devices']:
                    stats['devices_skipped_duplicate'] += 1
                    continue
                created['devices'].add(uid)

                photo_requirement = self._clean(self._get(row, ASSET_COLUMNS['photo_requirement']))
                photo_required = photo_requirement != PHOTO_NOT_REQUIRED_TAG
                if photo_requirement == PHOTO_REQUIRED_TAG:
                    photo_required = True

                _device, device_created = InspectionDevice.objects.update_or_create(
                    store_inspection=inspection, client_device_uid=uid,
                    defaults={
                        'asset': asset,
                        'asset_id_text': asset_id,
                        'category': normalize_device_category(category_raw),
                        'brand_model': brand_model,
                        'sn': device_sn,
                        'usage': self._clean(self._get(row, ASSET_COLUMNS['usage'])),
                        'warranty_start': self._parse_date(self._get(row, ASSET_COLUMNS['warranty_start'])),
                        'photo_required': photo_required,
                        'outline': self._clean(self._get(row, ASSET_COLUMNS['outline'])),
                        'device_notes': self._clean(self._get(row, ASSET_COLUMNS['device_notes'])),
                        'status': InspectionDevice.Status.IN_STORE,
                        'is_new_device': False,
                    },
                )
                if device_created:
                    stats['devices'] += 1
                    if jda in per_store:
                        per_store[jda]['devices'] += 1
                self._record(_device, device_created)

            if self._run is not None:
                finalize_import_run(
                    self._run, created=self._seq, updated=0,
                    skipped=stats['devices_skipped_duplicate'],
                    notes='Kering master import (schedule + asset list)',
                )

            if options['dry_run']:
                transaction.set_rollback(True)

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

    # -- helpers -------------------------------------------------------------
    def _record(self, instance, created):
        """Track a created object for rollback (no-op when tracking is disabled)."""
        if created and getattr(self, '_run', None) is not None:
            self._seq += 1
            record_import_change(self._run, self._seq, 'create', instance)

    def _ensure_asset(self, company, inspection, category_raw, brand_model, sn, asset_id, warranty_start, stats):
        """Get-or-create the Asset (and its category/brand/model) for a device row.

        Category/Brand have UNIQUE `code` (and Brand a UNIQUE `name`); real Kering
        data has case/whitespace variants that would collide, so we look up by code
        first, then name, and only create when neither exists.
        """
        category_name = (normalize_device_category(category_raw) or category_raw or 'Other')[:255]
        category_code = self._category_code(category_name)
        category = (
            AssetCategory.objects.filter(code=category_code).first()
            or AssetCategory.objects.filter(name=category_name).first()
        )
        cat_created = category is None
        if cat_created:
            category = AssetCategory.objects.create(name=category_name, code=category_code)
            stats['categories'] += 1
        self._record(category, cat_created)

        brand_name, model_name = self._split_brand_model(brand_model)
        brand_name = brand_name[:255]
        brand_code = (brand_name[:20].upper().replace(' ', '') or 'NA')
        brand = (
            AssetBrand.objects.filter(code=brand_code).first()
            or AssetBrand.objects.filter(name=brand_name).first()
        )
        brand_created = brand is None
        if brand_created:
            brand = AssetBrand.objects.create(name=brand_name, code=brand_code)
            stats['brands'] += 1
        self._record(brand, brand_created)

        model = None
        if model_name:
            model, model_created = AssetModel.objects.get_or_create(
                brand=brand, model_number=model_name[:100],
                defaults={'name': model_name[:255], 'category': category},
            )
            if model_created:
                stats['models'] += 1
            self._record(model, model_created)

        lookup_sn = '' if is_placeholder_identifier(sn) else sn
        clean_asset_id = '' if is_placeholder_identifier(asset_id) else asset_id
        asset_defaults = {
            'category': category, 'brand': brand, 'model': model,
            'division': inspection.division, 'location': inspection.location,
            'warranty_start_date': warranty_start, 'status': Asset.AssetStatus.AVAILABLE,
        }
        # asset_number is UNIQUE: only reuse the Kering Asset ID if it is free, else
        # let Asset auto-generate one (InspectionDevice.asset_id_text keeps the real ID).
        asset_id_to_use = clean_asset_id
        if asset_id_to_use and Asset.objects.filter(company=company, asset_number=asset_id_to_use).exists():
            asset_id_to_use = ''

        # Key on SN first (primary device identifier), then Asset ID; otherwise the
        # row has no stable identity so always create a fresh Asset.
        if lookup_sn:
            asset, asset_created = Asset.objects.get_or_create(
                company=company, serial_number=lookup_sn,
                defaults={**asset_defaults, 'asset_number': asset_id_to_use},
            )
        elif asset_id_to_use:
            asset, asset_created = Asset.objects.get_or_create(
                company=company, asset_number=asset_id_to_use,
                defaults={**asset_defaults, 'serial_number': ''},
            )
        else:
            asset = Asset.objects.create(
                company=company, serial_number='', asset_number='', **asset_defaults,
            )
            asset_created = True
        if asset_created:
            stats['assets'] += 1
        self._record(asset, asset_created)
        return asset

    def _read_rows(self, path):
        """Read a workbook/CSV into a list of dict rows."""
        import pandas as pd
        ext = os.path.splitext(path)[1].lower()
        if ext == '.csv':
            from utils.csv_import import read_csv_rows_with_fallback
            with open(path, 'rb') as handle:
                reader, _encoding = read_csv_rows_with_fallback(handle)
                return list(reader)
        dataframe = pd.read_excel(path)
        return dataframe.to_dict('records')

    def _get(self, row, candidates):
        for key in candidates:
            if key in row and row[key] is not None:
                return row[key]
        return ''

    def _clean(self, value):
        if value is None:
            return ''
        text = ' '.join(str(value).strip().split())
        return '' if text.lower() in ('nan', 'none', 'nat') else text

    def _clean_identifier(self, value):
        """Normalize an SN / Asset ID, clearing placeholder values to blank."""
        text = self._clean(value)
        if is_placeholder_identifier(text):
            return ''
        # Guard against Excel turning long numeric SNs into floats/scientific notation.
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return text

    def _normalize_jda(self, value):
        text = self._clean(value)
        if not text:
            return ''
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return text.split('.')[0] if text.replace('.', '', 1).isdigit() else text

    def _parse_date(self, value):
        """Parse a workbook cell into a date; return None for blanks/NaN/NaT.

        pandas reads empty date cells as NaT (not float NaN), and NaT.date() yields
        NaT again - which Django rejects on save ('NaTType does not support
        utcoffset'). Guard every branch with pd.isna.
        """
        import pandas as pd
        if value is None:
            return None
        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass
        if hasattr(value, 'date'):
            try:
                parsed = value.date()
            except Exception:
                parsed = None
            if parsed is not None and not pd.isna(parsed):
                return parsed
        text = self._clean(value)
        if not text:
            return None
        parsed = pd.to_datetime(text, errors='coerce')
        try:
            if pd.isna(parsed):
                return None
        except (TypeError, ValueError):
            pass
        return parsed.date()

    def _split_brand_model(self, brand_model):
        """Best-effort split of a Kering 'Brand-Model' string into (brand, model)."""
        text = self._clean(brand_model)
        if not text:
            return 'Unknown', ''
        if '-' in text:
            brand, _, model = text.partition('-')
            return (brand.strip() or 'Unknown'), model.strip()
        parts = text.split(' ', 1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
        return text, ''

    def _category_code(self, category_name):
        base = ''.join(ch for ch in category_name if ch.isalnum())[:12].upper()
        return base or 'CAT'
