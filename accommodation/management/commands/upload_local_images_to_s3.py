import mimetypes
import os

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

local_directory = "espacil_images"
prefix_on_s3 = "import-espacil2"


def upload_image_to_s3(image_path, file_name):
    s3 = boto3.client(
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

    bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    mime_type = mimetypes.guess_type(file_name)[0] or "image/jpeg"

    file_key = f"{prefix_on_s3}/{file_name}"

    with open(image_path, "rb") as f:
        try:
            s3.put_object(
                Bucket=bucket_name,
                Key=file_key,
                Body=f,
                ContentType=mime_type,
                ACL="public-read",
            )
            print(f"Image {file_name} uploaded {file_key}")
            return f"{settings.AWS_S3_PUBLIC_BASE_URL}/{file_key}"
        except ClientError as e:
            print(f"Error uploading {file_name}: {e}")
            return None


def upload_images_in_directory(directory_path):
    if not os.path.isdir(directory_path):
        print(f"Local dir {directory_path} doesnot exist.")
        return

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)

        if os.path.isfile(file_path) and filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
            print(f"Uploading {filename}...")
            upload_image_to_s3(file_path, filename)


if __name__ == "__main__":
    upload_images_in_directory(local_directory)
