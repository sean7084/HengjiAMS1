from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='productprice',
            options={
                'ordering': ['brand__name', 'model__name', '-is_current', '-valid_from', '-updated_at'],
                'verbose_name': 'Product Price',
                'verbose_name_plural': 'Product Prices',
            },
        ),
        migrations.AlterUniqueTogether(
            name='productprice',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='productprice',
            constraint=models.UniqueConstraint(
                condition=Q(('is_current', True)),
                fields=('model',),
                name='uniq_current_product_price_per_model',
            ),
        ),
    ]