from django.apps import apps
from django.db import transaction
from django.utils import timezone
from django.core.files.base import File

from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from companies.models import ImportRun, ImportRunChange


def snapshot_instance(instance):
    """Serialize concrete model fields (except PK) into JSON-compatible dict."""

    def _json_safe(value):
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, File):
            return value.name
        return str(value)

    data = {}
    for field in instance._meta.concrete_fields:
        if field.primary_key:
            continue
        raw_value = field.value_from_object(instance)
        data[field.name] = _json_safe(raw_value)
    return data


def start_import_run(user, module, import_type, total_rows=0):
    return ImportRun.objects.create(
        user=user,
        module=module,
        import_type=import_type,
        total_rows=total_rows,
    )


def finalize_import_run(run, created=0, updated=0, skipped=0, error_count=0, notes=''):
    run.created_count = created
    run.updated_count = updated
    run.skipped_count = skipped
    run.error_count = error_count
    run.notes = notes
    if created > 0 or updated > 0:
        run.status = ImportRun.RunStatus.COMPLETED
    else:
        run.status = ImportRun.RunStatus.FAILED
    run.save(update_fields=[
        'created_count',
        'updated_count',
        'skipped_count',
        'error_count',
        'notes',
        'status',
    ])


def record_import_change(run, sequence, operation, instance, row_number=None, before_data=None, after_data=None):
    ImportRunChange.objects.create(
        run=run,
        sequence=sequence,
        row_number=row_number,
        app_label=instance._meta.app_label,
        model_name=instance._meta.model_name,
        object_pk=str(instance.pk),
        operation=operation,
        before_data=before_data or {},
        after_data=after_data or {},
    )


def get_latest_rollback_run(user, module, import_type):
    if not user or not user.is_authenticated:
        return None
    return ImportRun.objects.filter(
        user=user,
        module=module,
        import_type=import_type,
        status=ImportRun.RunStatus.COMPLETED,
        rolled_back_at__isnull=True,
    ).order_by('-created_at').first()


def _restore_instance(instance, before_data):
    field_names = []
    for field in instance._meta.concrete_fields:
        if field.primary_key or field.name not in before_data:
            continue
        setattr(instance, field.name, before_data[field.name])
        field_names.append(field.name)

    if field_names:
        instance.save(update_fields=field_names)


def rollback_run(run):
    """Rollback a completed import run. Returns dict with counters and errors."""
    result = {
        'deleted': 0,
        'restored': 0,
        'errors': [],
    }

    if not run or not run.can_rollback:
        result['errors'].append('Run is not rollback-eligible.')
        return result

    with transaction.atomic():
        changes = run.changes.order_by('-sequence', '-id')
        for change in changes:
            model_class = apps.get_model(change.app_label, change.model_name)
            if model_class is None:
                result['errors'].append(
                    f"Unable to resolve model {change.app_label}.{change.model_name}."
                )
                continue

            obj = model_class.objects.filter(pk=change.object_pk).first()

            if change.operation == ImportRunChange.ChangeOperation.CREATE:
                if obj is not None:
                    obj.delete()
                    result['deleted'] += 1
                continue

            if change.operation == ImportRunChange.ChangeOperation.UPDATE:
                if obj is None:
                    result['errors'].append(
                        f"Cannot restore missing object {change.app_label}.{change.model_name}#{change.object_pk}."
                    )
                    continue
                _restore_instance(obj, change.before_data or {})
                result['restored'] += 1

        run.status = ImportRun.RunStatus.ROLLED_BACK
        run.rolled_back_at = timezone.now()
        run.save(update_fields=['status', 'rolled_back_at'])

    return result
