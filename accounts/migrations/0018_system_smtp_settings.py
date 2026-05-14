from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0017_normalize_blank_employee_ids'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemSMTPSettings',
            fields=[
                ('id', models.PositiveSmallIntegerField(default=1, editable=False, primary_key=True, serialize=False)),
                ('from_email', models.EmailField(max_length=254, verbose_name='From Email')),
                ('from_display_name', models.CharField(blank=True, max_length=150, verbose_name='From Display Name')),
                ('username', models.CharField(blank=True, max_length=255, verbose_name='SMTP Username')),
                ('encrypted_password', models.TextField(blank=True, verbose_name='Encrypted Password')),
                ('smtp_host', models.CharField(max_length=255, verbose_name='SMTP Host')),
                ('smtp_port', models.PositiveIntegerField(default=587, verbose_name='SMTP Port')),
                ('smtp_security', models.CharField(choices=[('none', 'None'), ('ssl_tls', 'SSL/TLS'), ('starttls', 'STARTTLS')], default='starttls', max_length=10, verbose_name='SMTP Security')),
                ('timeout', models.PositiveIntegerField(default=15, verbose_name='Connection Timeout')),
                ('is_active', models.BooleanField(default=False, verbose_name='Active')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name': 'System SMTP Settings',
                'verbose_name_plural': 'System SMTP Settings',
            },
        ),
    ]