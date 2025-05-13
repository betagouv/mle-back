import mimetypes
import uuid

import boto3
import requests
from botocore.config import Config
from django.conf import settings
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from account.models import Owner
from account.serializers import OwnerSerializer
from common.serializers import BinaryToBase64Field

from .models import Accommodation, ExternalSource


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


class AccommodationImportSerializer(serializers.ModelSerializer):
    source_id = serializers.CharField(write_only=True, required=False, default=None, allow_null=True)
    source = serializers.CharField(write_only=True)
    images_content = serializers.ListField(child=BinaryToBase64Field(), required=False, default=None)
    images_urls = serializers.ListField(child=serializers.CharField(), required=False, default=None)
    owner_id = serializers.CharField(write_only=True, required=False, default=None, allow_null=True)

    class Meta:
        model = Accommodation
        fields = (
            "name",
            "address",
            "geom",
            "city",
            "postal_code",
            "residence_type",
            "nb_total_apartments",
            "nb_accessible_apartments",
            "nb_coliving_apartments",
            "nb_t1",
            "nb_t1_bis",
            "nb_t2",
            "nb_t3",
            "nb_t4_more",
            "price_min_t1",
            "price_max_t1",
            "price_min_t1_bis",
            "price_max_t1_bis",
            "price_min_t2",
            "price_max_t2",
            "price_min_t3",
            "price_max_t3",
            "price_min_t4_more",
            "price_max_t4_more",
            "laundry_room",
            "common_areas",
            "bike_storage",
            "parking",
            "secure_access",
            "residence_manager",
            "kitchen_type",
            "desk",
            "cooking_plates",
            "microwave",
            "refrigerator",
            "bathroom",
            "external_url",
            "source_id",
            "source",
            "images_urls",
            "images_content",
            "owner_id",
        )

    def create(self, validated_data):
        source_id = validated_data.pop("source_id")
        source = validated_data.pop("source")
        images_urls = validated_data.pop("images_urls") or []
        images_content = validated_data.pop("images_content") or []
        owner_id = validated_data.pop("owner_id", None)

        if source_id and source:
            accommodation = Accommodation.objects.filter(sources__source_id=source_id, sources__source=source).first()

        if not accommodation:
            accommodation, _ = Accommodation.objects.get_or_create(
                name=validated_data["name"],
                address=validated_data["address"],
                city=validated_data["city"],
                postal_code=validated_data["postal_code"],
            )

        fields = (
            "geom",
            "residence_type",
            "nb_total_apartments",
            "nb_accessible_apartments",
            "nb_coliving_apartments",
            "nb_t1",
            "nb_t1_bis",
            "nb_t2",
            "nb_t3",
            "nb_t4_more",
            "price_min_t1",
            "price_max_t1",
            "price_min_t1_bis",
            "price_max_t1_bis",
            "price_min_t2",
            "price_max_t2",
            "price_min_t3",
            "price_max_t3",
            "price_min_t4_more",
            "price_max_t4_more",
            "laundry_room",
            "common_areas",
            "bike_storage",
            "parking",
            "secure_access",
            "residence_manager",
            "kitchen_type",
            "desk",
            "cooking_plates",
            "microwave",
            "refrigerator",
            "bathroom",
            "external_url",
        )
        accommodation_fields = {}
        for field_name in fields:
            if validated_data.get(field_name) is not None:
                # do not erase values on update
                accommodation_fields[field_name] = validated_data.pop(field_name, None)

        for field_name, field_value in accommodation_fields.items():
            if field_value is not None:
                # do not erase values on update
                setattr(accommodation, field_name, field_value)

        image_urls = []
        for img_data in images_content + images_urls:
            if isinstance(img_data, str) and img_data.startswith("http"):
                img_data = requests.get(img_data).content
            url = upload_image_to_s3(img_data)
            image_urls.append(url)

        accommodation.images_urls = image_urls

        if owner_id:
            owner = Owner.objects.get(pk=owner_id)
            accommodation.owner = owner

        accommodation.save()

        ExternalSource.objects.get_or_create(
            accommodation=accommodation,
            source=source,
            defaults={"source_id": source_id},
        )

        return accommodation


class BaseAccommodationSerialiser(serializers.Serializer):
    price_min = serializers.SerializerMethodField()
    price_max = serializers.SerializerMethodField()

    def get_price_min(self, obj) -> int:
        prices = [obj.price_min_t1, obj.price_min_t1_bis, obj.price_min_t2, obj.price_min_t3, obj.price_min_t4_more]
        prices = [p for p in prices if p is not None]
        return min(prices) if prices else None

    def get_price_max(self, obj) -> int:
        prices = [obj.price_max_t1, obj.price_max_t1_bis, obj.price_max_t2, obj.price_max_t3, obj.price_max_t4_more]
        prices = [p for p in prices if p is not None]
        return max(prices) if prices else None


class AccommodationDetailSerializer(BaseAccommodationSerialiser, serializers.ModelSerializer):
    owner = OwnerSerializer(read_only=True)

    class Meta:
        model = Accommodation
        fields = (
            "id",
            "name",
            "slug",
            "address",
            "city",
            "postal_code",
            "residence_type",
            "nb_total_apartments",
            "nb_accessible_apartments",
            "nb_coliving_apartments",
            "nb_t1",
            "nb_t1_bis",
            "nb_t2",
            "nb_t3",
            "nb_t4_more",
            "price_min",
            "price_max",
            "price_min_t1",
            "price_max_t1",
            "price_min_t1_bis",
            "price_max_t1_bis",
            "price_min_t2",
            "price_max_t2",
            "price_min_t3",
            "price_max_t3",
            "price_min_t4_more",
            "price_max_t4_more",
            "laundry_room",
            "common_areas",
            "bike_storage",
            "parking",
            "secure_access",
            "residence_manager",
            "kitchen_type",
            "desk",
            "cooking_plates",
            "microwave",
            "refrigerator",
            "bathroom",
            "geom",
            "images_urls",
            "owner",
        )


class AccommodationGeoSerializer(BaseAccommodationSerialiser, GeoFeatureModelSerializer):
    class Meta:
        model = Accommodation
        geo_field = "geom"
        fields = (
            "id",
            "name",
            "slug",
            "city",
            "postal_code",
            "nb_total_apartments",
            "nb_accessible_apartments",
            "nb_coliving_apartments",
            "price_min",
            "images_urls",
        )
