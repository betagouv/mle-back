import requests
from django.core.exceptions import ValidationError
from django.utils.translation import gettext
from drf_spectacular.utils import OpenApiTypes, extend_schema_field
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from account.models import Owner
from account.serializers import OwnerSerializer
from common.serializers import BinaryToBase64Field

from .models import Accommodation, ExternalSource, FavoriteAccommodation
from .utils import upload_image_to_s3


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
            "description",
            "address",
            "geom",
            "city",
            "postal_code",
            "residence_type",
            "nb_total_apartments",
            "nb_accessible_apartments",
            "nb_coliving_apartments",
            "nb_t1",
            "nb_t1_available",
            "nb_t1_bis",
            "nb_t1_bis_available",
            "nb_t2",
            "nb_t2_available",
            "nb_t3",
            "nb_t3_available",
            "nb_t4_more",
            "nb_t4_more_available",
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
            "accept_waiting_list",
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
        images_urls = validated_data.pop("images_urls") or None
        images_content = validated_data.pop("images_content") or None
        owner_id = validated_data.pop("owner_id", None)
        accommodation = None

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
            "description",
            "geom",
            "residence_type",
            "nb_total_apartments",
            "nb_accessible_apartments",
            "nb_coliving_apartments",
            "nb_t1",
            "nb_t1_available",
            "nb_t1_bis",
            "nb_t1_bis_available",
            "nb_t2",
            "nb_t2_available",
            "nb_t3",
            "nb_t3_available",
            "nb_t4_more",
            "nb_t4_more_available",
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
            "accept_waiting_list",
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
        if images_content is not None or images_urls is not None:
            for img_data in (images_content or []) + (images_urls or []):
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

    def validate(self, data):
        pairs = [
            ("nb_t1", "nb_t1_available"),
            ("nb_t1_bis", "nb_t1_bis_available"),
            ("nb_t2", "nb_t2_available"),
            ("nb_t3", "nb_t3_available"),
            ("nb_t4_more", "nb_t4_more_available"),
        ]

        errors = {}

        for stock_field, available_field in pairs:
            stock = data.get(stock_field, getattr(self.instance, stock_field, None) if self.instance else None)
            available = data.get(
                available_field, getattr(self.instance, available_field, None) if self.instance else None
            )

            if stock is not None and available is not None and available > stock:
                errors[available_field] = gettext(
                    "The number of available %(available)d is greater than the total %(total)d"
                ) % {"available": available, "total": stock}

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        try:
            instance = super().create(validated_data)
            instance.full_clean()
            instance.save()
            return instance
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)


class AccommodationDetailSerializer(BaseAccommodationSerialiser, serializers.ModelSerializer):
    owner = OwnerSerializer(read_only=True)

    class Meta:
        model = Accommodation
        fields = (
            "id",
            "name",
            "description",
            "slug",
            "address",
            "city",
            "postal_code",
            "residence_type",
            "nb_total_apartments",
            "nb_accessible_apartments",
            "nb_coliving_apartments",
            "nb_t1",
            "nb_t1_available",
            "nb_t1_bis",
            "nb_t1_bis_available",
            "nb_t2",
            "nb_t2_available",
            "nb_t3",
            "nb_t3_available",
            "nb_t4_more",
            "nb_t4_more_available",
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
            "external_url",
            "available",
            "accept_waiting_list",
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
            "available",
            "nb_t1_available",
            "nb_t1_bis_available",
            "nb_t2_available",
            "nb_t3_available",
            "nb_t4_more_available",
            "accept_waiting_list",
        )
        read_only_fields = ("id", "slug", "owner")


class MyAccommodationGeoSerializer(BaseAccommodationSerialiser, GeoFeatureModelSerializer):
    class Meta:
        model = Accommodation
        geo_field = "geom"
        fields = (
            "id",
            "name",
            "description",
            "slug",
            "address",
            "city",
            "postal_code",
            "nb_total_apartments",
            "nb_accessible_apartments",
            "nb_coliving_apartments",
            "images_urls",
            "available",
            "nb_t1",
            "nb_t1_available",
            "price_min_t1",
            "price_max_t1",
            "nb_t1_bis",
            "nb_t1_bis_available",
            "price_min_t1_bis",
            "price_max_t1_bis",
            "nb_t2",
            "nb_t2_available",
            "price_min_t2",
            "price_max_t2",
            "nb_t3",
            "nb_t3_available",
            "price_min_t3",
            "price_max_t3",
            "nb_t4_more",
            "nb_t4_more_available",
            "price_min_t4_more",
            "price_max_t4_more",
            "accept_waiting_list",
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
            "updated_at",
        )
        read_only_fields = ("id", "slug", "owner", "price_min", "updated_at")


class FavoriteAccommodationGeoSerializer(serializers.ModelSerializer):
    geom = serializers.SerializerMethodField()
    accommodation = AccommodationGeoSerializer(read_only=True)
    accommodation_slug = serializers.SlugRelatedField(
        slug_field="slug", queryset=Accommodation.objects.all(), write_only=True
    )

    class Meta:
        model = FavoriteAccommodation
        fields = ("id", "accommodation", "accommodation_slug", "created_at", "geom")

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_geom(self, obj):
        if obj.accommodation and obj.accommodation.geom:
            return {
                "type": "Point",
                "coordinates": [obj.accommodation.geom.x, obj.accommodation.geom.y],
            }
        return None

    def create(self, validated_data):
        accommodation = validated_data.pop("accommodation_slug")
        favorite, _ = FavoriteAccommodation.objects.get_or_create(
            user=self.context["request"].user, accommodation=accommodation
        )
        return favorite
