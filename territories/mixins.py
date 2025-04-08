from django.db.models import Sum
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from accommodation.models import Accommodation


class BBoxMixin(serializers.ModelSerializer):
    bbox = serializers.SerializerMethodField()

    @extend_schema_field(
        serializers.DictField(
            child=serializers.FloatField(), help_text="Bounding box with xmin, ymin, xmax, ymax coordinates"
        )
    )
    def get_bbox(self, obj):
        return obj.get_bbox()


class CityMixin(serializers.ModelSerializer):
    nb_total_apartments = serializers.SerializerMethodField()
    nb_coliving_apartments = serializers.SerializerMethodField()
    nb_t1 = serializers.SerializerMethodField()
    nb_t1_bis = serializers.SerializerMethodField()
    nb_t2 = serializers.SerializerMethodField()
    nb_t3 = serializers.SerializerMethodField()
    nb_t4_more = serializers.SerializerMethodField()

    def _get_city_stats(self, obj):
        if not hasattr(self, "_city_stats_cache"):
            self._city_stats_cache = {}

        if obj.id not in self._city_stats_cache:
            stats = Accommodation.objects.filter(city__iexact=obj.name, postal_code__in=obj.postal_codes).aggregate(
                nb_total_apartments=Sum("nb_total_apartments"),
                nb_coliving_apartments=Sum("nb_coliving_apartments"),
                nb_t1=Sum("nb_t1"),
                nb_t1_bis=Sum("nb_t1_bis"),
                nb_t2=Sum("nb_t2"),
                nb_t3=Sum("nb_t3"),
                nb_t4_more=Sum("nb_t4_more"),
            )
            self._city_stats_cache[obj.id] = {k: v or 0 for k, v in stats.items()}
        return self._city_stats_cache[obj.id]

    @extend_schema_field(serializers.IntegerField(help_text="Number of T1 apartments in the city"))
    def get_nb_t1(self, obj):
        return self._get_city_stats(obj)["nb_t1"]

    @extend_schema_field(serializers.IntegerField(help_text="Number of T1bis apartments in the city"))
    def get_nb_t1_bis(self, obj):
        return self._get_city_stats(obj)["nb_t1_bis"]

    @extend_schema_field(serializers.IntegerField(help_text="Number of T2 apartments in the city"))
    def get_nb_t2(self, obj):
        return self._get_city_stats(obj)["nb_t2"]

    @extend_schema_field(serializers.IntegerField(help_text="Number of T3 apartments in the city"))
    def get_nb_t3(self, obj):
        return self._get_city_stats(obj)["nb_t3"]

    @extend_schema_field(serializers.IntegerField(help_text="Number of T4+ apartments in the city"))
    def get_nb_t4_more(self, obj):
        return self._get_city_stats(obj)["nb_t4_more"]

    @extend_schema_field(serializers.IntegerField(help_text="Number of coliving accommodations in the city"))
    def get_nb_coliving_apartments(self, obj):
        return self._get_city_stats(obj)["nb_coliving_apartments"]

    @extend_schema_field(serializers.IntegerField(help_text="Number of accommodations in the city"))
    def get_nb_total_apartments(self, obj):
        return self._get_city_stats(obj)["nb_total_apartments"]
