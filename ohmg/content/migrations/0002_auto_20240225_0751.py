# Generated by Django 3.2.18 on 2024-02-25 07:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="page",
            name="published",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="page",
            name="title",
            field=models.CharField(
                help_text="Title will be slugified and must not conflict with other Pages or Places. Place slugs are formatted as follows: 'united-states', 'orleans-parish-la', and 'new-orleans-la'.",
                max_length=200,
            ),
        ),
    ]
