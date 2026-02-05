from django.db import migrations
from django.db.models import Func, Value, F, TextField

flags = Value('g')

def fix_postal_slugs(apps, schema_editor):
    # Get the historical version of your model
    Page = apps.get_model('frontend', 'Page')
    Page.objects.filter(slug__regex=r'-ka$').update(
        F("slug"),
        Value(r'(.+)-ka$'),
        Value(r'\1-ks'),
        flags,
        function='REGEXP_REPLACE',
        output_field=TextField(),
    )
    Page.objects.filter(slug__regex=r'-cn$').update(
        F("slug"),
        Value(r'(.+)-cn$'),
        Value(r'\1-ct'),
        flags,
        function='REGEXP_REPLACE',
        output_field=TextField(),
    )


def rebreak_postal_slugs(apps, schema_editor):
    Page = apps.get_model('frontend', 'Page')
    Page.objects.filter(slug__regex=r'-ks$').update(
        F("slug"),
        Value(r'(.+)-ks$'),
        Value(r'\1-ka'),
        flags,
        function='REGEXP_REPLACE',
        output_field=TextField(),
    )
    Page.objects.filter(slug__regex=r'-ct$').update(
        F("slug"),
        Value(r'(.+)-ct$'),
        Value(r'\1-cn'),
        flags,
        function='REGEXP_REPLACE',
        output_field=TextField(),
    )



class Migration(migrations.Migration):

    operations = [
        migrations.RunPython(fix_postal_slugs, rebreak_postal_slugs),
    ]
