import os
import re

from django.conf import settings

from accommodation.management.commands.upload_base_command import UploadS3BaseCommand

local_directory = "temp/crous_images/"
prefix_on_s3 = "crous-images"
image_regexp = None


class Command(UploadS3BaseCommand):
    help = "Upload CROUS images to S3, keeping the same directory structure to have predictive paths"

    def handle(self, *args, **options):
        if not os.path.isdir(local_directory):
            print(f"Local dir {local_directory} does not exist.")
            return
        images_urls = []
        for root, _, files in os.walk(local_directory):
            for filename in files:
                if image_regexp is not None and re.match(image_regexp, filename) is None:
                    continue
                file_path = os.path.join(root, filename)
                if os.path.isfile(file_path) and filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                    relative_path = os.path.relpath(file_path, local_directory).replace("\\", "/")
                    s3_key = f"{prefix_on_s3}/{relative_path}"
                    if self.s3_key_exists(s3_key):
                        print(f"Skipping {file_path}, already exists on S3")
                        continue
                    print(f"Uploading {file_path}...")
                    self.upload_image_to_s3(file_path, prefix_on_s3, relative_path)
                    images_urls.append(f"{settings.AWS_S3_PUBLIC_BASE_URL}/{s3_key}")
                    print(f"Uploaded to {s3_key}")
        print(f"Images for {local_directory}:")
        print("|".join(images_urls))
