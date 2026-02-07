import mimetypes
import uuid

import boto3
from botocore.config import Config
from django.conf import settings
from geopy.geocoders import BANFrance


def upload_image_to_s3(binary_data, file_extension=".jpg"):
    s3 = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=Config(request_checksum_calculation="when_required", response_checksum_validation="when_required"),
    )

    bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_key = f"accommodations{settings.AWS_SUFFIX_DIR}/{unique_filename}"

    mime_type = mimetypes.guess_type(unique_filename)[0] or "image/jpeg"

    s3.put_object(
        Bucket=bucket_name,
        Key=file_key,
        Body=bytes(binary_data),
        ContentType=mime_type,
        ACL="public-read",
    )

    return f"{settings.AWS_S3_PUBLIC_BASE_URL}/{file_key}"


def snapshot_model(instance):
    """
    Take a snapshot of all concrete model fields.
    """
    IGNORED_FIELDS = {"id", "created_at", "updated_at", "geom"}
    return {
        field.name: getattr(instance, field.name) for field in instance._meta.fields if field.name not in IGNORED_FIELDS
    }


def compute_model_diff(instance, old_data, *, fields):
    """
    Compute a diff between old_data and the current state of instance.

    Only the given fields are considered.

    Returns:
        {
            field_name: {"old": old_value, "new": new_value}
        }
    """
    diff = {}

    for name in fields:
        old_value = old_data.get(name)
        new_value = getattr(instance, name)

        if old_value != new_value:
            diff[name] = {
                "old": old_value,
                "new": new_value,
            }

    return diff
def get_geolocator():
    return BANFrance()
