import json

from django.conf import settings
from django.core.management.base import BaseCommand
import boto3

from ohmg.core.utils import confirm_continue


class Command(BaseCommand):
    help = (
        "Create and set permissions on S3 bucket. S3 credentials and configs "
        "(bucket name, region, and endpoint URL) can be provided, or will default"
        "to env variables."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--bucket",
            default=settings.AWS_STORAGE_BUCKET_NAME,
            help="Optionally provide a bucket name, uses AWS_STORAGE_BUCKET_NAME if not provided.",
        )
        parser.add_argument(
            "--region",
            default=settings.AWS_S3_REGION_NAME,
            help="Optionally provide a region name, uses AWS_S3_REGION_NAME if not provided.",
        )
        parser.add_argument(
            "--endpoint-url",
            default=settings.AWS_S3_ENDPOINT_URL,
            help="Optionally provide a custom endpoint URL, uses AWS_S3_ENDPOINT_URL if not provided.",
        )
        parser.add_argument(
            "--access-key-id",
            default=settings.AWS_ACCESS_KEY_ID,
            help="Optionally provide access key id, uses AWS_ACCESS_KEY_ID if not provided.",
        )
        parser.add_argument(
            "--secret-access-key",
            default=settings.AWS_SECRET_ACCESS_KEY,
            help="Optionally provide a secret access key, uses AWS_SECRET_ACCESS_KEY if not provided.",
        )

    def handle(self, *args, **options):
        bucket_name = options["bucket"]
        endpoint_url = options["endpoint_url"]
        region_name = options["region"]
        access_id = options["access_key_id"]
        secret_key = options["secret_access_key"]

        print("Initializing bucket")
        print(f"Bucket name:    {bucket_name}")
        print(f"Region:         {region_name}")
        print(f"Endpoint URL:   {endpoint_url}")

        confirm_continue()

        client = boto3.client(
            "s3",
            aws_access_key_id=access_id,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url,
            region_name=region_name,
        )

        ## create bucket if it doesn't exist
        response = client.list_buckets()
        if bucket_name not in [i["Name"] for i in response["Buckets"]]:
            print(f"Creating bucket: {bucket_name}")
            client.create_bucket(Bucket=bucket_name)
            print("Bucket created.")
        else:
            print(f"Bucket already exists: {bucket_name}")
            confirm_continue(
                "Do you want to overwrite this bucket's " "CORS configuration and access policy?",
                default="n",
            )

        ## set CORS
        cors_configuration = {
            "CORSRules": [
                {
                    "AllowedHeaders": ["*"],
                    "AllowedMethods": ["GET"],
                    "AllowedOrigins": ["*"],
                    "ExposeHeaders": [
                        "x-amz-server-side-encryption",
                        "x-amz-request-id",
                        "x-amz-id-2",
                    ],
                    "MaxAgeSeconds": 3000,
                }
            ]
        }
        client.put_bucket_cors(Bucket=bucket_name, CORSConfiguration=cors_configuration)
        print("CORS configured:")
        print(json.dumps(cors_configuration, indent=2))

        ## set bucket policy
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicRead",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    "Resource": f"arn:aws:s3:::{bucket_name}/*",
                }
            ],
        }

        # Set the new policy
        client.put_bucket_policy(
            Bucket=bucket_name,
            # Convert the policy from JSON dict to string
            Policy=json.dumps(bucket_policy),
        )
        print("Bucket policy updated:")
        print(json.dumps(bucket_policy, indent=2))
