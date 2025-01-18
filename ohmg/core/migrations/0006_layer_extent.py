# Generated by Django 3.2.18 on 2025-01-14 22:23

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_remove_layer_extent'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='extent',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), blank=True, null=True, size=4),
        ),
    ]