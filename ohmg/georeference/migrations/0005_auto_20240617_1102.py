# Generated by Django 3.2.18 on 2024-06-17 11:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('georeference', '0004_alter_setcategory_options'),
    ]

    operations = [
        migrations.RenameModel('Layer', 'LayerV1'),
        migrations.AlterField(
            model_name='sessionbase',
            name='lyr',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lyr', to='georeference.layerv1'),
        ),
    ]
