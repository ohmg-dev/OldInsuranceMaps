from pathlib import Path

from django.conf import settings


def get_boto3_s3_client():
    import boto3

    if settings.AWS_ACCESS_KEY_ID:
        return boto3.client(
            "s3",
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        )
    else:
        return None


def upload_file_to_bucket(local_path, bucket_path, client=None):
    if not client:
        client = get_boto3_s3_client()
    client.upload_file(local_path, settings.AWS_STORAGE_BUCKET_NAME, bucket_path)


# def upload_directory_to_bucket(local_path, bucket_path, client=None):
#     if not client:
#         client = get_boto3_s3_client()


def upload_directory_to_bucket(local_path: Path, bucket_path: str, client=None):
    if not client:
        client = get_boto3_s3_client()
    for file_path in local_path.rglob("*"):
        if file_path.is_file():
            # Get relative path, format for S3 (replace backslashes)
            s3_key = str(file_path.relative_to(local_path)).replace("\\", "/")
            if bucket_path:
                s3_key = f"{bucket_path}/{s3_key}"
            upload_file_to_bucket(file_path, s3_key, client=client)
