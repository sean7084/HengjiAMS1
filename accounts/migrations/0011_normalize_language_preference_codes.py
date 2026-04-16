from django.db import migrations, models


def normalize_language_preferences(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    code_map = {
        'en': 'en-us',
        'en-us': 'en-us',
        'zh-cn': 'zh-cn',
        'zh-hans': 'zh-cn',
        'zh-hant': 'zh-cn',
    }

    for user in User.objects.all().only('id', 'language_preference'):
        normalized = code_map.get((user.language_preference or '').lower(), 'en-us')
        if user.language_preference != normalized:
            user.language_preference = normalized
            user.save(update_fields=['language_preference'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_user_force_2fa_setup'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='language_preference',
            field=models.CharField(
                choices=[('en-us', 'English (US)'), ('zh-cn', 'Chinese (Simplified)')],
                default='en-us',
                max_length=10,
                verbose_name='Language Preference',
            ),
        ),
        migrations.RunPython(normalize_language_preferences, migrations.RunPython.noop),
    ]
