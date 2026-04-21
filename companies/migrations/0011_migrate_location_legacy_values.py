from django.db import migrations


def migrate_location_legacy_values(apps, schema_editor):
    Location = apps.get_model('companies', 'Location')

    status_map = {
        'inactive': 'closed',
        'maintenance': 'under_construction',
    }
    type_map = {
        'building': 'other',
        'floor': 'other',
        'room': 'other',
        'factory': 'other',
    }

    for old_value, new_value in status_map.items():
        Location.objects.filter(status=old_value).update(status=new_value)

    for old_value, new_value in type_map.items():
        Location.objects.filter(location_type=old_value).update(location_type=new_value)

    Location.objects.filter(code='').update(code=None)


def reverse_migrate_location_legacy_values(apps, schema_editor):
    # Data remap is intentionally one-way to keep normalized vocabulary.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0010_location_chinese_address_location_code_2_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_location_legacy_values, reverse_migrate_location_legacy_values),
    ]
