from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import Accommodation


class AccommodationGeoSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Accommodation
        geo_field = "geom"
        fields = (
            "id",
            "name",
            "slug",
            "address",
            "city",
            "postal_code",
            "residence_type",
            "owner_name",
            "owner_url",
            "nb_total_apartments",
            "nb_accessible_apartments",
            "nb_coliving_apartments",
            "nb_t1",
            "nb_t1_bis",
            "nb_t2",
            "nb_t3",
            "nb_t4_more",
        )
