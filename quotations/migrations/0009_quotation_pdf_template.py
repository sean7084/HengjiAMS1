from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quotations', '0008_quotation_remarks'),
    ]

    operations = [
        migrations.AddField(
            model_name='quotation',
            name='pdf_template',
            field=models.CharField(
                choices=[('v2_full', 'V2 Full'), ('v2_mini', 'V2 Mini'), ('v1', 'V1')],
                default='v2_full',
                max_length=20,
                verbose_name='PDF Template',
            ),
        ),
    ]