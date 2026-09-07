"""Re-encrypt stored mailbox/SMTP passwords from legacy XOR to Fernet.

Before this migration, ``encrypted_password`` values were produced by the old
``_xor_secret`` helper (reversible XOR keyed on SECRET_KEY). This data migration
reads each stored value, decrypts it (transparently handling the legacy XOR
scheme via ``accounts.crypto.decrypt_secret``), and re-encrypts it with Fernet.

The migration is idempotent: values that are already valid Fernet tokens are
skipped, and values that cannot be decrypted are left untouched (no data loss).
"""

from django.db import migrations


def reencrypt_to_fernet(apps, schema_editor):
    from accounts.crypto import decrypt_secret, encrypt_secret, is_fernet_token

    UserMailboxSettings = apps.get_model('accounts', 'UserMailboxSettings')
    SystemSMTPSettings = apps.get_model('accounts', 'SystemSMTPSettings')

    for model in (UserMailboxSettings, SystemSMTPSettings):
        for instance in model.objects.all():
            stored = instance.encrypted_password
            # Skip empty values and anything already migrated to Fernet.
            if not stored or is_fernet_token(stored):
                continue
            plaintext = decrypt_secret(stored)
            if not plaintext:
                # Could not decrypt (corrupted/unknown format) - leave as-is.
                continue
            instance.encrypted_password = encrypt_secret(plaintext)
            instance.save(update_fields=['encrypted_password'])


def noop_reverse(apps, schema_editor):
    """Reverting to insecure XOR obfuscation is intentionally not supported."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0018_system_smtp_settings'),
    ]

    operations = [
        migrations.RunPython(reencrypt_to_fernet, noop_reverse),
    ]
