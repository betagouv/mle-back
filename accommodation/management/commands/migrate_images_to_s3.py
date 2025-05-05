import mimetypes

import boto3
from botocore.config import Config
from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from accommodation.models import Accommodation


class Command(BaseCommand):
    help = "Migrate Accommodation images from DB to OVH S3"

    def handle(self, *args, **options):
        s3 = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=Config(
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )

        bucket = settings.AWS_STORAGE_BUCKET_NAME

        accommodations = Accommodation.objects.filter(images__isnull=False).exclude(images=[])
        self.stdout.write(f"Found {accommodations.count()} accommodations with images to migrate")

        for accommodation in tqdm(accommodations, desc="Migrating accommodations"):
            new_images_urls = accommodation.images_urls or []

            for idx, binary_data in enumerate(accommodation.images or []):
                mime_type = mimetypes.guess_type(f"file{idx}")[0] or "image/jpeg"
                extension = mimetypes.guess_extension(mime_type) or ".jpg"

                file_key = f"accommodations{settings.AWS_SUFFIX_DIR}/{accommodation.id}/{idx}{extension}"

                self.stdout.write(f"Uploading to {bucket} with key {file_key} and content type {mime_type}")
                self.stdout.write(f"Size of data: {len(binary_data)}")

                try:
                    s3.put_object(
                        Bucket=bucket,
                        Key=file_key,
                        Body=bytes(binary_data),
                        ContentType=mime_type,
                    )

                    public_url = f"{settings.AWS_S3_PUBLIC_BASE_URL}/{file_key}"
                    new_images_urls.append(public_url)

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Erreur lors de l'upload de {file_key}: {e}"))

            accommodation.images_urls = new_images_urls
            accommodation.save()

        self.stdout.write(self.style.SUCCESS("Migration complete!"))
