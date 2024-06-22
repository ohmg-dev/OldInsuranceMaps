import os
import boto3
from argparse import Namespace

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.test.client import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "generate-error-pages",
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

        if options['operation'] == "generate-error-pages":
            rf = RequestFactory()
            request = rf.get('/')
            middleware = SessionMiddleware(lambda x: None)
            middleware.process_request(request)
            request.session.save()
            request.user = Namespace(is_authenticated=False)
            for status in [404, 500]:
                content = render_to_string(f'{status}.html.template', request=request)
                outpath = os.path.join(settings.PROJECT_DIR, f"frontend/templates/{status}.html")
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
