# Generated manually on 2026-05-07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("report", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="datarun",
            name="run_title",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
