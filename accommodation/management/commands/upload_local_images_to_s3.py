import os
import re

from django.conf import settings

from accommodation.management.commands.upload_base_command import UploadS3BaseCommand

local_directory = "temp/evolea_images/"
prefix_on_s3 = "evolea-images"
image_regexp = None  # r"^9021.*\.jpg"


class Command(UploadS3BaseCommand):
    help = "Upload images to S3"

    def handle(self, *args, **options):
        if not os.path.isdir(local_directory):
            print(f"Local dir {local_directory} doesnot exist.")
            return

        images_urls = []
        for filename in os.listdir(local_directory):
            if image_regexp is not None and re.match(image_regexp, filename) is None:
                print(f"Ignore file {filename} not matching image_regexp")
                continue
            file_path = os.path.join(local_directory, filename)

            if os.path.isfile(file_path) and filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                print(f"Uploading {filename}...")
                self.upload_image_to_s3(file_path, prefix_on_s3)
                print(f"File uploaded to S3 with URL: {settings.AWS_S3_PUBLIC_BASE_URL}/{prefix_on_s3}/{filename}")
                images_urls.append(f"{settings.AWS_S3_PUBLIC_BASE_URL}/{prefix_on_s3}/{filename}")

        print(f"Images for {local_directory}:")
        print("|".join(images_urls))
