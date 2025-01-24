# Generated by Django 3.2.18 on 2024-09-14 15:25

import django.contrib.postgres.fields
from django.db import migrations, models
import ohmg.georeference.models


class Migration(migrations.Migration):

    dependencies = [
        ('georeference', '0008_auto_20240823_1921'),
    ]

    operations = [
        migrations.AddField(
            model_name='layerset',
            name='extent',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), blank=True, null=True, size=4),
        ),
        migrations.AlterField(
            model_name='sessionlock',
            name='expiration',
            field=models.DateTimeField(default=ohmg.georeference.models.default_expiration_time),
        ),
    ]
