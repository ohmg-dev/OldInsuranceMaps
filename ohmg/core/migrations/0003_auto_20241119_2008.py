# Generated by Django 3.2.18 on 2024-11-19 20:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20240901_1331'),
    ]

    operations = [
        migrations.AddField(
            model_name='map',
            name='featured',
            field=models.BooleanField(default=False, help_text='show in featured section'),
        ),
        migrations.AddField(
            model_name='map',
            name='hidden',
            field=models.BooleanField(default=False, help_text='this map will be excluded from api calls (but url available directly)'),
        ),
        migrations.AlterField(
            model_name='map',
            name='status',
            field=models.CharField(choices=[('not started', 'not started'), ('initializing...', 'initializing...'), ('document load error', 'document load error'), ('ready', 'ready')], default='not started', max_length=50),
        ),
    ]