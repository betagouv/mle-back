import requests
from django.core.exceptions import ValidationError
from django.utils.translation import gettext
from drf_spectacular.utils import OpenApiTypes, extend_schema_field
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.gis.geos import Point

from account.models import Owner
from account.serializers import OwnerSerializer
from common.serializers import BinaryToBase64Field

from .models import Accommodation, AccommodationApplication, ExternalSource, FavoriteAccommodation
from .utils import get_geolocator, upload_image_to_s3
from territories.services import get_city_manager_service


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
            "nb_t4",
            "nb_t4_available",
            "nb_t5",
            "nb_t5_available",
            "nb_t6",
            "nb_t6_available",
            "nb_t7_more",
            "nb_t7_more_available",
            "price_min_t1",
            "price_max_t1",
            "price_min_t1_bis",
            "price_max_t1_bis",
            "price_min_t2",
            "price_max_t2",
            "price_min_t3",
            "price_max_t3",
            "price_min_t4",
            "price_max_t4",
            "price_min_t5",
            "price_max_t5",
            "price_min_t6",
            "price_max_t6",
            "price_min_t7_more",
            "price_max_t7_more",
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
            "wifi",
            "bathroom",
            "accept_waiting_list",
            "scholarship_holders_priority",
            "external_url",
            "source_id",
            "source",
            "images_urls",
            "images_content",
            "owner_id",
        )

    def _update_fields(self, accommodation, validated_data):
        for field_name, field_value in validated_data.items():
            if field_value is not None:
                setattr(accommodation, field_name, field_value)
        return accommodation

    def _manage_images(self, accommodation, images_content, images_urls):
        image_urls = []
        if images_content is not None or images_urls is not None:
            for img_data in (images_content or []) + (images_urls or []):
                if isinstance(img_data, str) and img_data.startswith("http"):
                    img_data = requests.get(img_data).content
                url = upload_image_to_s3(img_data)
                image_urls.append(url)
            accommodation.images_urls = image_urls
        return accommodation

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

        accommodation = self._update_fields(accommodation, validated_data)

        if owner_id:
            owner = Owner.objects.get(pk=owner_id)
            accommodation.owner = owner

        accommodation = self._manage_images(accommodation, images_content, images_urls)

        accommodation.save()

        ExternalSource.objects.get_or_create(
            accommodation=accommodation,
            source=source,
            defaults={"source_id": source_id},
        )

        return accommodation

    def update(self, instance, validated_data):
        images_urls = validated_data.pop("images_urls", None)
        images_content = validated_data.pop("images_content", None)
        owner_id = validated_data.pop("owner_id", None)

        instance = self._update_fields(instance, validated_data)

        if owner_id:
            owner = Owner.objects.get(pk=owner_id)
            instance.owner = owner

        instance = self._manage_images(instance, images_content, images_urls)
        instance.save()
        return instance


class BaseAccommodationSerialiser(serializers.Serializer):
    price_min = serializers.SerializerMethodField()
    price_max = serializers.SerializerMethodField()

    def get_price_min(self, obj) -> int:
        prices = [
            obj.price_min_t1,
            obj.price_min_t1_bis,
            obj.price_min_t2,
            obj.price_min_t3,
            obj.price_min_t4,
            obj.price_min_t5,
            obj.price_min_t6,
            obj.price_min_t7_more,
        ]
        prices = [p for p in prices if p is not None]
        return min(prices) if prices else None

    def get_price_max(self, obj) -> int:
        prices = [
            obj.price_max_t1,
            obj.price_max_t1_bis,
            obj.price_max_t2,
            obj.price_max_t3,
            obj.price_max_t4,
            obj.price_max_t5,
            obj.price_max_t6,
            obj.price_max_t7_more,
        ]
        prices = [p for p in prices if p is not None]
        return max(prices) if prices else None

    def validate(self, data):
        pairs = [
            ("nb_t1", "nb_t1_available"),
            ("nb_t1_bis", "nb_t1_bis_available"),
            ("nb_t2", "nb_t2_available"),
            ("nb_t3", "nb_t3_available"),
            ("nb_t4", "nb_t4_available"),
            ("nb_t5", "nb_t5_available"),
            ("nb_t6", "nb_t6_available"),
            ("nb_t7_more", "nb_t7_more_available"),
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
            "nb_t4",
            "nb_t4_available",
            "nb_t5",
            "nb_t5_available",
            "nb_t6",
            "nb_t6_available",
            "nb_t7_more",
            "nb_t7_more_available",
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
            "price_min_t4",
            "price_max_t4",
            "price_min_t5",
            "price_max_t5",
            "price_min_t6",
            "price_max_t6",
            "price_min_t7_more",
            "price_max_t7_more",
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
            "wifi",
            "bathroom",
            "geom",
            "images_urls",
            "owner",
            "external_url",
            "available",
            "accept_waiting_list",
            "scholarship_holders_priority",
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
            "published",
            "nb_t1",
            "nb_t1_available",
            "nb_t1_bis",
            "nb_t1_bis_available",
            "nb_t2",
            "nb_t2_available",
            "nb_t3",
            "nb_t3_available",
            "nb_t4",
            "nb_t4_available",
            "nb_t5",
            "nb_t5_available",
            "nb_t6",
            "nb_t6_available",
            "nb_t7_more",
            "nb_t7_more_available",
            "accept_waiting_list",
            "scholarship_holders_priority",
        )
        read_only_fields = ("id", "slug", "owner")


class MyAccommodationSerializer(BaseAccommodationSerialiser, serializers.ModelSerializer):
    images_files = serializers.ListField(child=serializers.FileField(), required=False, default=None, write_only=True)

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
            "nb_total_apartments",
            "nb_accessible_apartments",
            "nb_coliving_apartments",
            "images_urls",
            "available",
            "nb_t1",
            "nb_t1_available",
            "nb_t1_bis",
            "nb_t1_bis_available",
            "nb_t2",
            "nb_t2_available",
            "nb_t3",
            "nb_t3_available",
            "nb_t4",
            "nb_t4_available",
            "nb_t5",
            "nb_t5_available",
            "nb_t6",
            "nb_t6_available",
            "nb_t7_more",
            "nb_t7_more_available",
            "price_min_t1",
            "price_max_t1",
            "price_min_t1_bis",
            "price_max_t1_bis",
            "price_min_t2",
            "price_max_t2",
            "price_min_t3",
            "price_max_t3",
            "price_min_t4",
            "price_max_t4",
            "price_min_t5",
            "price_max_t5",
            "price_min_t6",
            "price_max_t6",
            "price_min_t7_more",
            "price_max_t7_more",
            "accept_waiting_list",
            "scholarship_holders_priority",
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
            "wifi",
            "bathroom",
            "external_url",
            "updated_at",
            "published",
            "images_files",
        )
        read_only_fields = ("id", "slug", "owner", "price_min", "updated_at", "images_urls")

    def create(self, validated_data):
        images_files = validated_data.pop("images_files") or None
        validated_data.setdefault("images_urls", [])
        if images_files:
            for image_file in images_files:
                binary_data = image_file.read()
                image_url = upload_image_to_s3(binary_data)
                validated_data["images_urls"].append(image_url)

        owner = validated_data.pop("owner")
        if not owner:
            raise serializers.ValidationError({"owner": "Owner not found"})
        validated_data["owner"] = owner

        # create city if not exists
        city_manager_service = get_city_manager_service()
        city = city_manager_service.get_or_create_city(validated_data.get("city"), validated_data.get("postal_code"))
        if not city:
            raise serializers.ValidationError({"city": "City not found"})

        address = validated_data.get("address")
        geolocator = get_geolocator()
        full_address = f"{address}, {validated_data.get('city')}, {validated_data.get('postal_code')}"
        coordinates = geolocator.geocode(full_address)
        if coordinates:
            validated_data["geom"] = Point(float(coordinates.longitude), float(coordinates.latitude), srid=4326)
        return super().create(validated_data)


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
            "nb_t1_bis",
            "nb_t1_bis_available",
            "nb_t2",
            "nb_t2_available",
            "nb_t3",
            "nb_t3_available",
            "nb_t4",
            "nb_t4_available",
            "nb_t5",
            "nb_t5_available",
            "nb_t6",
            "nb_t6_available",
            "nb_t7_more",
            "nb_t7_more_available",
            "price_min_t1",
            "price_max_t1",
            "price_min_t1_bis",
            "price_max_t1_bis",
            "price_min_t2",
            "price_max_t2",
            "price_min_t3",
            "price_max_t3",
            "price_min_t4",
            "price_max_t4",
            "price_min_t5",
            "price_max_t5",
            "price_min_t6",
            "price_max_t6",
            "price_min_t7_more",
            "price_max_t7_more",
            "accept_waiting_list",
            "scholarship_holders_priority",
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
            "wifi",
            "bathroom",
            "external_url",
            "updated_at",
            "published",
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


class AccommodationApplicationSerializer(serializers.ModelSerializer):
    accommodation_slug = serializers.CharField(source="accommodation.slug", read_only=True)

    class Meta:
        model = AccommodationApplication
        fields = (
            "id",
            "accommodation_slug",
            "status",
            "dossierfacile_status",
            "dossierfacile_url",
            "dossierfacile_pdf_url",
            "created_at",
        )
        read_only_fields = fields


class OwnerAccommodationApplicationSerializer(serializers.ModelSerializer):
    accommodation_slug = serializers.CharField(source="accommodation.slug", read_only=True)
    accommodation_name = serializers.CharField(source="accommodation.name", read_only=True)
    student_email = serializers.EmailField(source="student.user.email", read_only=True)
    student_first_name = serializers.CharField(source="student.user.first_name", read_only=True)
    student_last_name = serializers.CharField(source="student.user.last_name", read_only=True)

    class Meta:
        model = AccommodationApplication
        fields = (
            "id",
            "status",
            "accommodation_slug",
            "accommodation_name",
            "student_email",
            "student_first_name",
            "student_last_name",
            "dossierfacile_status",
            "dossierfacile_url",
            "dossierfacile_pdf_url",
            "created_at",
        )
