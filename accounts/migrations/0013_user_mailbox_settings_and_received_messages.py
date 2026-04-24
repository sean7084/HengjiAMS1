from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_admin_roles_m2m'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserMailboxSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_address', models.EmailField(max_length=254, verbose_name='Email Address')),
                ('display_name', models.CharField(blank=True, max_length=150, verbose_name='Display Name')),
                ('username', models.CharField(max_length=255, verbose_name='Login Username')),
                ('encrypted_password', models.TextField(blank=True, verbose_name='Encrypted Password')),
                ('receive_protocol', models.CharField(choices=[('imap', 'IMAP'), ('pop3', 'POP3')], default='imap', max_length=10, verbose_name='Receive Protocol')),
                ('imap_host', models.CharField(blank=True, max_length=255, verbose_name='IMAP Host')),
                ('imap_port', models.PositiveIntegerField(default=993, verbose_name='IMAP Port')),
                ('imap_security', models.CharField(choices=[('none', 'None'), ('ssl_tls', 'SSL/TLS'), ('starttls', 'STARTTLS')], default='ssl_tls', max_length=10, verbose_name='IMAP Security')),
                ('pop3_host', models.CharField(blank=True, max_length=255, verbose_name='POP3 Host')),
                ('pop3_port', models.PositiveIntegerField(default=995, verbose_name='POP3 Port')),
                ('pop3_security', models.CharField(choices=[('none', 'None'), ('ssl_tls', 'SSL/TLS'), ('starttls', 'STARTTLS')], default='ssl_tls', max_length=10, verbose_name='POP3 Security')),
                ('smtp_host', models.CharField(max_length=255, verbose_name='SMTP Host')),
                ('smtp_port', models.PositiveIntegerField(default=465, verbose_name='SMTP Port')),
                ('smtp_security', models.CharField(choices=[('none', 'None'), ('ssl_tls', 'SSL/TLS'), ('starttls', 'STARTTLS')], default='ssl_tls', max_length=10, verbose_name='SMTP Security')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('last_connection_test_at', models.DateTimeField(blank=True, null=True, verbose_name='Last Connection Test At')),
                ('last_connection_status', models.CharField(blank=True, max_length=40, verbose_name='Last Connection Status')),
                ('last_connection_message', models.TextField(blank=True, verbose_name='Last Connection Message')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='mailbox_settings', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={'verbose_name': 'User Mailbox Settings', 'verbose_name_plural': 'User Mailbox Settings'},
        ),
        migrations.CreateModel(
            name='ReceivedEmailMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_id', models.CharField(max_length=255, verbose_name='External ID')),
                ('message_id', models.CharField(blank=True, max_length=255, verbose_name='Message-ID')),
                ('folder_name', models.CharField(blank=True, max_length=120, verbose_name='Folder')),
                ('subject', models.CharField(blank=True, max_length=255, verbose_name='Subject')),
                ('sender', models.CharField(blank=True, max_length=255, verbose_name='Sender')),
                ('recipients', models.TextField(blank=True, verbose_name='Recipients')),
                ('received_at', models.DateTimeField(blank=True, null=True, verbose_name='Received At')),
                ('body_preview', models.TextField(blank=True, verbose_name='Body Preview')),
                ('body_text', models.TextField(blank=True, verbose_name='Body Text')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='Metadata')),
                ('is_read', models.BooleanField(default=False, verbose_name='Read')),
                ('synced_at', models.DateTimeField(auto_now=True, verbose_name='Synced At')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('mailbox', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_messages', to='accounts.usermailboxsettings', verbose_name='Mailbox')),
            ],
            options={'verbose_name': 'Received Email Message', 'verbose_name_plural': 'Received Email Messages', 'ordering': ['-received_at', '-id']},
        ),
        migrations.AddConstraint(
            model_name='receivedemailmessage',
            constraint=models.UniqueConstraint(fields=('mailbox', 'external_id'), name='uniq_mailbox_external_message'),
        ),
    ]