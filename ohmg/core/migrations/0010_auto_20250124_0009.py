# Generated by Django 3.2.18 on 2025-01-24 00:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20250123_2104'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='document',
            options={'verbose_name_plural': '   Documents'},
        ),
        migrations.AlterModelOptions(
            name='layer',
            options={'verbose_name_plural': ' Layers'},
        ),
        migrations.AlterModelOptions(
            name='layerset',
            options={'verbose_name_plural': 'Layer Sets'},
        ),
        migrations.AlterModelOptions(
            name='layersetcategory',
            options={'verbose_name_plural': 'Layer Set Categories'},
        ),
        migrations.AlterModelOptions(
            name='map',
            options={'verbose_name_plural': '    Maps'},
        ),
        migrations.AlterModelOptions(
            name='mapgroup',
            options={'verbose_name_plural': '      Map Groups'},
        ),
        migrations.AlterModelOptions(
            name='region',
            options={'verbose_name_plural': '  Regions'},
        ),
    ]
