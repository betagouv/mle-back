import mimetypes

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management.base import BaseCommand


class UploadS3BaseCommand(BaseCommand):
    help = "Base class for upload to s3 commands"

    def get_s3_client(self):
        return boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=boto3.session.Config(
                signature_version="s3v4",
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )

    def s3_key_exists(self, key):
        s3 = self.get_s3_client()
        resp = s3.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Prefix=key, MaxKeys=1)
        return "Contents" in resp and any(obj["Key"] == key for obj in resp["Contents"])

    def upload_image_to_s3(self, image_path, s3_prefix, s3_relative_path=None):
        s3 = self.get_s3_client()
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
        if s3_relative_path:
            file_key = f"{s3_prefix}/{s3_relative_path}"
        else:
            import os

            file_key = f"{s3_prefix}/{os.path.basename(image_path)}"
        with open(image_path, "rb") as f:
            try:
                s3.put_object(
                    Bucket=bucket_name,
                    Key=file_key,
                    Body=f,
                    ContentType=mime_type,
                    ACL="public-read",
                )
                return f"{settings.AWS_S3_PUBLIC_BASE_URL}/{file_key}"
            except ClientError as e:
                print(f"Error uploading {image_path}: {e}")
                return None
