import base64

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from account.models import Owner
from account.serializers import OwnerSerializer
from common.serializers import BinaryToBase64Field

from .models import Accommodation, ExternalSource


class AccommodationImportSerializer(serializers.ModelSerializer):
    source_id = serializers.CharField(write_only=True)
    source = serializers.CharField(write_only=True)
    images = serializers.ListField(child=BinaryToBase64Field(), required=False, default=None)
    owner_id = serializers.CharField(write_only=True, required=False)

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
            "images",
            "owner_id",
        )

    def create(self, validated_data):
        source_id = validated_data.pop("source_id")
        source = validated_data.pop("source")
        images = validated_data.pop("images", [])
        owner_id = validated_data.pop("owner_id", None)

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
            accommodation_fields[field_name] = validated_data.pop(field_name, None)

        for field_name, field_value in accommodation_fields.items():
            setattr(accommodation, field_name, field_value)

        accommodation.images = images

        if owner_id and (owner_data := self.get_owner_data(owner_id)):
            owner, _ = Owner.objects.get_or_create(source_id=owner_id, defaults=owner_data)
            accommodation.owner = owner

        accommodation.save()

        source, _ = ExternalSource.objects.get_or_create(
            accommodation=accommodation,
            source=source,
            defaults={"source_id": source_id},
        )

        return accommodation


class BaseAccommodationSerialiser(serializers.Serializer):
    images_base64 = serializers.SerializerMethodField()
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

    def get_images_base64(self, obj) -> list[str]:
        images = obj.images or []
        images_base64 = []

        for image in images:
            encoded_image = base64.b64encode(image).decode("utf-8")
            images_base64.append(f"data:image/jpeg;base64,{encoded_image}")

        return images_base64


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
            "images_base64",
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
            "images_base64",
        )
