from django.db import migrations


def migrate_service_prices_to_service_items(apps, schema_editor):
    AssetModel = apps.get_model('assets', 'AssetModel')
    ProductPrice = apps.get_model('products', 'ProductPrice')
    ServiceItem = apps.get_model('products', 'ServiceItem')

    db_alias = schema_editor.connection.alias
    service_models = AssetModel.objects.using(db_alias).filter(category__item_type='service').select_related('brand', 'category')
    service_item_cache = {}

    for asset_model in service_models:
        service_group = ''
        if getattr(asset_model, 'category_id', None) and getattr(asset_model.category, 'name', ''):
            service_group = (asset_model.category.name or '').strip()
        elif getattr(asset_model, 'brand_id', None) and getattr(asset_model.brand, 'name', ''):
            brand_name = (asset_model.brand.name or '').strip()
            if brand_name.lower() not in {'service', 'services'}:
                service_group = brand_name

        service_name = (asset_model.name or asset_model.description or 'Service').strip()
        cache_key = (service_group, service_name)
        service_item = service_item_cache.get(cache_key)
        if service_item is None:
            service_item, _ = ServiceItem.objects.using(db_alias).get_or_create(
                service_group=service_group,
                name=service_name,
                defaults={
                    'description': (asset_model.description or '').strip(),
                    'unit': ((asset_model.unit or 'JOB').strip() or 'JOB'),
                    'is_active': asset_model.is_active,
                },
            )
            service_item_cache[cache_key] = service_item

        ProductPrice.objects.using(db_alias).filter(model_id=asset_model.pk).update(
            brand_id=None,
            model_id=None,
            service_item_id=service_item.pk,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_serviceitem_alter_productprice_options_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_service_prices_to_service_items, migrations.RunPython.noop),
    ]