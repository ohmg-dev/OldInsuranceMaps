# Generated by Django 3.2.18 on 2024-08-21 11:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('georeference', '0008_auto_20240821_1008'),
    ]

    operations = [
        migrations.AddField(
            model_name='layerset',
            name='map',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.map'),
        ),
    ]
