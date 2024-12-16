from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework.test import APITestCase

from .factories import AccommodationFactory


class AccommodationListAPITests(APITestCase):
    def setUp(self):
        self.accommodation_paris = AccommodationFactory(geom=Point(2.35, 48.85))
        self.accommodation_lyon = AccommodationFactory(geom=Point(4.85, 45.75))
        self.accommodation_unpublished = AccommodationFactory(published=False)
        self.accommodation_no_geom = AccommodationFactory(geom=None)

        self.accommodation_nantes_accessible = AccommodationFactory(
            geom=Point(-1.5536, 47.2184), nb_accessible_apartments=2
        )
        self.accommodation_nantes_non_accessible = AccommodationFactory(
            geom=Point(-1.5530, 47.2150), nb_accessible_apartments=0
        )

    def test_accommodation_list_no_filter(self):
        response = self.client.get(reverse("accommodation-list"))

        assert response.status_code == 200
        results = response.json()

        assert results["count"] == 4
        assert results["page_size"] == 30
        assert results["next"] is None and results["previous"] is None
        assert len(results["results"]["features"]) == 4
        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert "slug" in results["results"]["features"][0]["properties"]
        assert self.accommodation_paris.id in returned_ids
        assert self.accommodation_lyon.id in returned_ids
        assert self.accommodation_unpublished.id not in returned_ids
        assert self.accommodation_no_geom.id not in returned_ids

    def test_accommodation_list_view_filters(self):
        bbox = "-1.60,47.20,-1.50,47.30"  # Nantes

        response = self.client.get(reverse("accommodation-list"), {"bbox": bbox})
        results = response.json()

        assert len(results["results"]["features"]) == 2

        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert self.accommodation_nantes_accessible.id in returned_ids
        assert self.accommodation_nantes_non_accessible.id in returned_ids

        response = self.client.get(reverse("accommodation-list"), {"bbox": bbox, "is_accessible": True})
        results = response.json()

        assert len(results["results"]["features"]) == 1

        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert self.accommodation_nantes_accessible.id in returned_ids
        assert self.accommodation_nantes_non_accessible.id not in returned_ids
