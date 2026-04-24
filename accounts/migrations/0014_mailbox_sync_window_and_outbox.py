from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_user_mailbox_settings_and_received_messages'),
    ]

    operations = [
        migrations.AddField(
            model_name='usermailboxsettings',
            name='auto_sync_enabled',
            field=models.BooleanField(default=True, verbose_name='Auto Sync Enabled'),
        ),
        migrations.AddField(
            model_name='usermailboxsettings',
            name='imap_sent_folder',
            field=models.CharField(default='Sent', max_length=120, verbose_name='IMAP Sent Folder'),
        ),
        migrations.AddField(
            model_name='usermailboxsettings',
            name='last_mailbox_sync_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Last Mailbox Sync At'),
        ),
        migrations.AddField(
            model_name='usermailboxsettings',
            name='sync_lookback_months',
            field=models.PositiveIntegerField(default=6, verbose_name='Sync Lookback Months'),
        ),
        migrations.AddField(
            model_name='usermailboxsettings',
            name='sync_outbox',
            field=models.BooleanField(default=True, verbose_name='Sync Outbox'),
        ),
        migrations.AddField(
            model_name='receivedemailmessage',
            name='direction',
            field=models.CharField(choices=[('inbox', 'Inbox'), ('outbox', 'Outbox')], default='inbox', max_length=10, verbose_name='Direction'),
        ),
        migrations.AddField(
            model_name='receivedemailmessage',
            name='sent_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Sent At'),
        ),
        migrations.AlterModelOptions(
            name='receivedemailmessage',
            options={'ordering': ['-received_at', '-sent_at', '-id'], 'verbose_name': 'Received Email Message', 'verbose_name_plural': 'Received Email Messages'},
        ),
        migrations.RemoveConstraint(
            model_name='receivedemailmessage',
            name='uniq_mailbox_external_message',
        ),
        migrations.AddConstraint(
            model_name='receivedemailmessage',
            constraint=models.UniqueConstraint(fields=('mailbox', 'direction', 'external_id'), name='uniq_mailbox_direction_external_message'),
        ),
    ]