import base64

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import Accommodation, ExternalSource, Owner


class Base64BinaryField(serializers.Field):
    def to_representation(self, value):
        if value:
            return base64.b64encode(value).decode("utf-8")
        return

    def to_internal_value(self, data):
        if data:
            try:
                return base64.b64decode(data)
            except (TypeError, ValueError):
                raise serializers.ValidationError("Invalid base64 data.")
        return


class AccommodationImportSerializer(serializers.ModelSerializer):
    source_id = serializers.CharField(write_only=True)
    images = serializers.ListField(child=Base64BinaryField(), required=False)
    owner_id = serializers.CharField(write_only=True)

    class Meta:
        model = Accommodation
        fields = (
            "name",
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
            "geom",
            "source_id",
            "images",
            "owner_id",
        )

    def create(self, validated_data):
        source_id = validated_data.pop("source_id")
        images = validated_data.pop("images", [])
        owner_id = validated_data.pop("owner_id", None)

        accommodation, _ = Accommodation.objects.get_or_create(
            name=validated_data["name"],
            address=validated_data["address"],
            city=validated_data["city"],
            postal_code=validated_data["postal_code"],
        )

        fields = (
            "residence_type",
            "nb_total_apartments",
            "nb_accessible_apartments",
            "nb_coliving_apartments",
            "nb_t1",
            "nb_t1_bis",
            "nb_t2",
            "nb_t3",
            "nb_t4_more",
            "geom",
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
            source=ExternalSource.SOURCE_CLEF,
        )

        source.source_id = source_id
        source.save()

        return accommodation


class AccommodationDetailSerializer(serializers.ModelSerializer):
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
            "geom",
        )


class AccommodationGeoSerializer(GeoFeatureModelSerializer):
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
        )
