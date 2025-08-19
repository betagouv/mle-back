import csv
import os

from django.db.models import Func, Value

from accommodation.management.commands.upload_base_command import UploadS3BaseCommand
from accommodation.models import Accommodation


class Command(UploadS3BaseCommand):
    help = "Import CROUS photos from a CSV file"

    def handle(self, *args, **options):
        csv_file_path = "crous_nb_and_photos.csv"

        if not os.path.exists(csv_file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {csv_file_path}"))
            return

        with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=",")
            for row in reader:
                name = row["Residence"].strip().title()
                print("Managing", name)
                acc_instance = (
                    Accommodation.objects.annotate(unaccent_name=Func("name", function="unaccent"))
                    .filter(unaccent_name__iexact=Func(Value(name), function="unaccent"))
                    .first()
                )
                if not acc_instance:
                    self.stderr.write(self.style.WARNING(f"Accommodation not found: {name}, skipping"))
                    continue

                s3_residence_name = "_".join([k.upper() for k in row["répertoire résidence"].split("_")])
                s3_prefix = f"crous-images/{s3_residence_name}"
                images = self.list_images_from_s3(s3_prefix)
                if not images:
                    s3_residence_name = s3_residence_name.replace("é", "e")
                    s3_prefix = f"crous-images/{s3_residence_name}"
                    images = self.list_images_from_s3(s3_prefix)
                    if not images:
                        self.stderr.write(self.style.WARNING(f"No images found for {name}, ({s3_prefix}) skipping"))
                        continue

                acc_instance.images_urls = (acc_instance.images_urls or []) + images
                acc_instance.images_urls = [
                    url for i, url in enumerate(acc_instance.images_urls) if url not in acc_instance.images_urls[:i]
                ]
                acc_instance.save()
