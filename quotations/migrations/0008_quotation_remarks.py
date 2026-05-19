from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quotations', '0007_backfill_quotationitem_service_item'),
    ]

    operations = [
        migrations.AddField(
            model_name='quotation',
            name='remarks',
            field=models.TextField(blank=True, default='', verbose_name='Remarks'),
            preserve_default=False,
        ),
    ]