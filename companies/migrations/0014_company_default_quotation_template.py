from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0013_companyuser_is_authorized_rfq_sender'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='default_quotation_template',
            field=models.CharField(
                choices=[('v2_full', 'V2 Full'), ('v2_mini', 'V2 Mini'), ('v1', 'V1')],
                default='v2_full',
                help_text='Default PDF template used for new quotations for this company',
                max_length=20,
                verbose_name='Default Quotation Template',
            ),
        ),
    ]