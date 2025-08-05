from rest_framework_gis.serializers import GeoFeatureModelSerializer

from institution.models import EducationalInstitution


class EducationalInstitutionGeoSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = EducationalInstitution
        geo_field = "geom"
        fields = (
            "id",
            "name",
            "city",
            "address",
            "postal_code",
            "website",
        )
