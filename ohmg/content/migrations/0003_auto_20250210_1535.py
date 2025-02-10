# Generated by Django 3.2.18 on 2025-02-10 15:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0002_auto_20240225_0751'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='extra_head',
            field=models.CharField(blank=True, max_length=600, null=True),
        ),
        migrations.AddField(
            model_name='page',
            name='render_as_html',
            field=models.BooleanField(default=False),
        ),
    ]
