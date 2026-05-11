from django.db import migrations


def normalize_blank_employee_ids(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(employee_id='').update(employee_id=None)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0016_split_order_management_role'),
    ]

    operations = [
        migrations.RunPython(normalize_blank_employee_ids, migrations.RunPython.noop),
    ]