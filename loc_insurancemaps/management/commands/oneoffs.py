import os
import csv
import boto3
from pathlib import Path

from django.db import transaction
from django.db.models.functions import Lower
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.test.client import RequestFactory

from loc_insurancemaps.models import Volume, Place

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "generate-500.html",
                "initialize-s3-bucket",
                "migrate-places",
                "connect-volumes-to-places",
                "reset-volume-counts",
            ],
            help="the identifier of the LoC resource to add",
        )
        parser.add_argument(
            "--layerid",
            help="the identifier of for the layer",
        )

    def handle(self, *args, **options):

        print(f"operation: {options['operation']}")

        if options['operation'] == "generate-500.html":
            rf = RequestFactory()
            request = rf.get('/')
            content = render_to_string('500.html.template', request=request)
            outpath = os.path.join(settings.LOCAL_ROOT, "templates/500.html")
            with open(outpath, 'w') as static_file:
                static_file.write(content)
            print(f"file saved to: {outpath}")

        if options['operation'] == "initialize-s3-bucket":
            client = boto3.client("s3", **settings.S3_CONFIG)

            response = client.list_buckets()
            if settings.S3_BUCKET_NAME not in [i['Name'] for i in response['Buckets']]:
                print(f"Creating bucket: {settings.S3_BUCKET_NAME}")
                client.create_bucket(Bucket=settings.S3_BUCKET_NAME)
                print("Bucket created.")
            else:
                print(f"Bucket already exists: {settings.S3_BUCKET_NAME}")
