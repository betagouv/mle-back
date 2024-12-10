from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework.test import APITestCase

from .factories import AccommodationFactory


class AccommodationListAPITests(APITestCase):
    def setUp(self):
        self.accommodation_paris = AccommodationFactory(geom=Point(2.35, 48.85))
        self.accommodation_lyon = AccommodationFactory(geom=Point(4.85, 45.75))
        self.accommodation_unpublished = AccommodationFactory(published=False)

    def test_accommodation_list_no_filter(self):
        response = self.client.get(reverse("accommodation-list"))

        assert response.status_code == 200
        results = response.json()

        assert results["count"] == 2
        assert results["next"] is None and results["previous"] is None
        assert len(results["results"]["features"]) == 2
        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert self.accommodation_paris.id in returned_ids
        assert self.accommodation_lyon.id in returned_ids
        assert self.accommodation_unpublished.id not in returned_ids

    def test_accommodation_list_view_bbox_filter(self):
        bbox = "2.30,48.80,2.40,48.90"

        response = self.client.get(reverse("accommodation-list"), {"bbox": bbox})

        assert response.status_code == 200
        results = response.json()

        assert results["count"] == 1
        assert results["next"] is None and results["previous"] is None
        assert len(results["results"]["features"]) == 1
        feature = results["results"]["features"][0]
        assert feature["id"] == self.accommodation_paris.id
