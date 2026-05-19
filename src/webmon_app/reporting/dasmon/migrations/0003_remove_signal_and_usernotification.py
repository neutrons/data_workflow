# Generated migration to remove obsolete Signal and UserNotification models
# ADARA/DASMON signals are no longer sent (confirmed by DAQ team April 14, 2026)

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("dasmon", "0002_delete_legacyurl"),
        ("report", "0001_initial"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Signal",
        ),
        migrations.DeleteModel(
            name="UserNotification",
        ),
    ]
