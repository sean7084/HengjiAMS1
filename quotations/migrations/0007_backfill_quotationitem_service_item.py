from django.db import migrations


def backfill_quotationitem_service_item(apps, schema_editor):
    QuotationItem = apps.get_model('quotations', 'QuotationItem')

    db_alias = schema_editor.connection.alias
    quotation_items = QuotationItem.objects.using(db_alias).filter(
        service_item__isnull=True,
        product_price__service_item__isnull=False,
    ).select_related('product_price__service_item')

    for item in quotation_items:
        item.service_item_id = item.product_price.service_item_id
        item.save(update_fields=['service_item'])


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_migrate_service_prices_to_service_items'),
        ('quotations', '0006_quotationitem_service_item'),
    ]

    operations = [
        migrations.RunPython(backfill_quotationitem_service_item, migrations.RunPython.noop),
    ]