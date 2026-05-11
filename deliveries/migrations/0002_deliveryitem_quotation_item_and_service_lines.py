from django.db import migrations, models
import django.db.models.deletion


def normalize_prepared_status(apps, schema_editor):
    DeliveryOrder = apps.get_model('deliveries', 'DeliveryOrder')
    DeliveryOrder.objects.filter(status='prepared').update(status='pending')


class Migration(migrations.Migration):

    dependencies = [
        ('quotations', '0005_quotation_requires_confirmation_and_more'),
        ('deliveries', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(normalize_prepared_status, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='deliveryorder',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('dispatched', 'Dispatched'), ('completed', 'Delivered')], default='pending', max_length=20, verbose_name='Status'),
        ),
        migrations.AlterField(
            model_name='deliveryitem',
            name='asset',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='delivery_items', to='assets.asset', verbose_name='Asset'),
        ),
        migrations.AddField(
            model_name='deliveryitem',
            name='quotation_item',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='delivery_items', to='quotations.quotationitem', verbose_name='Quotation Item'),
        ),
    ]