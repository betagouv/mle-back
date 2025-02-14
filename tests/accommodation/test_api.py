from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework.test import APITestCase

from .factories import AccommodationFactory


class AccommodationDetailAPITests(APITestCase):
    def setUp(self):
        self.accommodation_published = AccommodationFactory(geom=Point(2.35, 48.85), published=True)
        self.accommodation_unpublished = AccommodationFactory(published=False)

    def test_accommodation_detail_success(self):
        response = self.client.get(reverse("accommodation-detail", kwargs={"slug": self.accommodation_published.slug}))

        assert response.status_code == 200
        result = response.json()

        assert result["id"] == self.accommodation_published.id
        assert result["slug"] == self.accommodation_published.slug
        assert result["name"] == self.accommodation_published.name
        assert result["geom"]["coordinates"] == [2.35, 48.85]

    def test_accommodation_detail_not_found_if_unpublished(self):
        response = self.client.get(
            reverse("accommodation-detail", kwargs={"slug": self.accommodation_unpublished.slug})
        )

        assert response.status_code == 404

    def test_accommodation_detail_404_if_invalid_id(self):
        response = self.client.get(reverse("accommodation-detail", kwargs={"slug": "unknown-slug-in-db"}))

        assert response.status_code == 404


class AccommodationListAPITests(APITestCase):
    def setUp(self):
        self.accommodation_paris = AccommodationFactory(geom=Point(2.35, 48.85))
        self.accommodation_lyon = AccommodationFactory(geom=Point(4.85, 45.75))
        self.accommodation_unpublished = AccommodationFactory(published=False)
        self.accommodation_no_geom = AccommodationFactory(geom=None)

        self.accommodation_nantes_accessible_w_coliving = AccommodationFactory(
            geom=Point(-1.5536, 47.2184), nb_accessible_apartments=2, nb_coliving_apartments=5
        )
        self.accommodation_nantes_non_accessible = AccommodationFactory(
            geom=Point(-1.5530, 47.2150), nb_accessible_apartments=0
        )
        self.accommodation_marseille_w_coliving = AccommodationFactory(
            geom=Point(5.3698, 43.2965), nb_coliving_apartments=1, nb_accessible_apartments=0
        )
        self.accommodation_marseille_wo_coliving = AccommodationFactory(
            geom=Point(5.3698, 43.2965), nb_coliving_apartments=0, nb_accessible_apartments=0
        )

    def test_accommodation_list_no_filter(self):
        response = self.client.get(reverse("accommodation-list"))

        assert response.status_code == 200
        results = response.json()

        assert results["count"] == 6
        assert results["page_size"] == 30
        assert results["next"] is None and results["previous"] is None
        assert len(results["results"]["features"]) == 6
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
        assert self.accommodation_nantes_accessible_w_coliving.id in returned_ids
        assert self.accommodation_nantes_non_accessible.id in returned_ids

        response = self.client.get(reverse("accommodation-list"), {"bbox": bbox, "is_accessible": True})
        results = response.json()

        assert len(results["results"]["features"]) == 1

        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert self.accommodation_nantes_accessible_w_coliving.id in returned_ids
        assert self.accommodation_nantes_non_accessible.id not in returned_ids

        bbox = "5.30,43.20,5.45,43.35"  # Marseille
        response = self.client.get(reverse("accommodation-list"), {"bbox": bbox, "has_coliving": True})
        results = response.json()

        assert len(results["results"]["features"]) == 1

        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert self.accommodation_marseille_w_coliving.id in returned_ids
        assert self.accommodation_marseille_wo_coliving.id not in returned_ids

        bbox = "-1.60,43.20,5.45,47.30"  # Nantes + Marseille

        response = self.client.get(
            reverse("accommodation-list"), {"bbox": bbox, "has_coliving": True, "is_accessible": True}
        )
        results = response.json()

        assert len(results["results"]["features"]) == 1

        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert self.accommodation_nantes_accessible_w_coliving.id in returned_ids

    def test_accommodation_list_center_radius(self):
        center = "-1.5536,47.2184"  # Nantes (near the accessible accommodation)

        response = self.client.get(reverse("accommodation-list"), {"center": center, "radius": 0.2})
        results = response.json()

        assert len(results["results"]["features"]) == 1

        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert self.accommodation_nantes_accessible_w_coliving.id in returned_ids
        assert self.accommodation_nantes_non_accessible.id not in returned_ids

        response = self.client.get(reverse("accommodation-list"), {"center": center, "radius": 2})
        results = response.json()

        assert len(results["results"]["features"]) == 2

        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert self.accommodation_nantes_accessible_w_coliving.id in returned_ids
        assert self.accommodation_nantes_non_accessible.id in returned_ids

        center_paris = "2.35,48.85"  # Paris

        response = self.client.get(reverse("accommodation-list"), {"center": center_paris, "radius": 10})
        results = response.json()

        assert len(results["results"]["features"]) == 1

        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert self.accommodation_paris.id in returned_ids
        assert self.accommodation_lyon.id not in returned_ids
        assert self.accommodation_nantes_accessible_w_coliving.id not in returned_ids
        assert self.accommodation_nantes_non_accessible.id not in returned_ids
