import base64

from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework.test import APITestCase

from tests.account.factories import OwnerFactory

from .factories import AccommodationFactory


class AccommodationDetailAPITests(APITestCase):
    def setUp(self):
        owner = OwnerFactory(name="Bailleur1", url="http://bailleur1.com", image=b"Bailleur1 logo")
        self.accommodation_published = AccommodationFactory(
            description="<p>Ceci est un beau texte en <b>gras</b></p>",
            geom=Point(2.35, 48.85),
            published=True,
            owner=owner,
            external_url="https://bailleur1.com/residence",
            available=True,
            nb_total_apartments=1,
            nb_accessible_apartments=1,
            nb_coliving_apartments=1,
            nb_t1=2,
            nb_t1_available=1,
        )
        self.accommodation_unpublished = AccommodationFactory(published=False, available=False)

    def test_accommodation_detail_success(self):
        response = self.client.get(reverse("accommodation-detail", kwargs={"slug": self.accommodation_published.slug}))

        assert response.status_code == 200
        result = response.json()

        assert result["id"] == self.accommodation_published.id
        assert result["slug"] == self.accommodation_published.slug
        assert result["name"] == self.accommodation_published.name
        assert result["description"] == self.accommodation_published.description
        assert result["geom"]["coordinates"] == [2.35, 48.85]
        assert result["owner"]["name"] == "Bailleur1"
        assert result["owner"]["image_base64"] == "data:image/jpeg;base64,{}".format(
            base64.b64encode(b"Bailleur1 logo").decode("utf-8")
        )
        assert result["external_url"] == "https://bailleur1.com/residence"
        assert result["available"] is True
        assert result["nb_total_apartments"] == self.accommodation_published.nb_total_apartments
        assert result["nb_accessible_apartments"] == self.accommodation_published.nb_accessible_apartments
        assert result["nb_coliving_apartments"] == self.accommodation_published.nb_coliving_apartments
        assert result["nb_t1"] == self.accommodation_published.nb_t1
        assert result["nb_t1_available"] == self.accommodation_published.nb_t1_available
        assert result["nb_t1_bis"] == self.accommodation_published.nb_t1_bis
        assert result["nb_t2"] == self.accommodation_published.nb_t2
        assert result["nb_t3"] == self.accommodation_published.nb_t3
        assert result["nb_t4_more"] == self.accommodation_published.nb_t4_more

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

        self.accommodation_nantes_accessible_w_coliving_cheap = AccommodationFactory(
            geom=Point(-1.5536, 47.2184),
            nb_accessible_apartments=2,
            nb_coliving_apartments=5,
            price_min_t1=300,
            nb_t1_available=2,
        )
        self.accommodation_nantes_non_accessible_expensive = AccommodationFactory(
            geom=Point(-1.5530, 47.2150), nb_accessible_apartments=0, price_min_t1=800
        )
        self.accommodation_marseille_w_coliving_expensive = AccommodationFactory(
            geom=Point(5.3698, 43.2965), nb_coliving_apartments=1, nb_accessible_apartments=0, price_min_t2=700
        )
        self.accommodation_marseille_wo_coliving_cheap = AccommodationFactory(
            geom=Point(5.3698, 43.2965), nb_coliving_apartments=0, nb_accessible_apartments=0, price_min_t1=400
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

        assert any(feature["properties"]["nb_t1_available"] == 2 for feature in results["results"]["features"])

    def test_accommodation_list_view_filters(self):
        bbox = "-1.60,47.20,-1.50,47.30"  # Nantes

        response = self.client.get(reverse("accommodation-list"), {"bbox": bbox})
        results = response.json()

        assert len(results["results"]["features"]) == 2

        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert self.accommodation_nantes_accessible_w_coliving_cheap.id in returned_ids
        assert self.accommodation_nantes_non_accessible_expensive.id in returned_ids

        response = self.client.get(reverse("accommodation-list"), {"bbox": bbox, "is_accessible": True})
        results = response.json()

        assert len(results["results"]["features"]) == 1

        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert self.accommodation_nantes_accessible_w_coliving_cheap.id in returned_ids
        assert self.accommodation_nantes_non_accessible_expensive.id not in returned_ids

        bbox = "5.30,43.20,5.45,43.35"  # Marseille
        response = self.client.get(reverse("accommodation-list"), {"bbox": bbox, "has_coliving": True})
        results = response.json()

        assert len(results["results"]["features"]) == 1

        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert self.accommodation_marseille_w_coliving_expensive.id in returned_ids
        assert self.accommodation_marseille_wo_coliving_cheap.id not in returned_ids

        bbox = "-1.60,43.20,5.45,47.30"  # Nantes + Marseille

        response = self.client.get(
            reverse("accommodation-list"), {"bbox": bbox, "has_coliving": True, "is_accessible": True}
        )
        results = response.json()

        assert len(results["results"]["features"]) == 1

        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert self.accommodation_nantes_accessible_w_coliving_cheap.id in returned_ids

        response = self.client.get(reverse("accommodation-list"), {"price_max": 600})
        results = response.json()

        assert len(results["results"]["features"]) == 2

        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert self.accommodation_nantes_accessible_w_coliving_cheap.id in returned_ids
        assert self.accommodation_marseille_wo_coliving_cheap.id in returned_ids

    def test_accommodation_list_excludes_null_price_min_with_price_max_filter(self):
        accommodation_null_price = AccommodationFactory(price_min=None)

        response = self.client.get(reverse("accommodation-list"), {"price_max": 600})
        results = response.json()
        returned_ids = [feature["id"] for feature in results["results"]["features"]]

        assert accommodation_null_price.id not in returned_ids

    def test_accommodation_list_pagination_preserves_query_params(self):
        for _ in range(40):
            AccommodationFactory(geom=Point(2.0, 48.0), published=True, price_min_t1=100)

        response = self.client.get(reverse("accommodation-list"), {"price_max": 600, "page_size": 30})
        assert response.status_code == 200

        data = response.json()
        next_url = data["next"]

        assert next_url is not None
        assert "price_max=600" in next_url
        assert "page=2" in next_url
        assert "page_size=30" in next_url

    def test_accommodation_list_center_radius(self):
        center = "-1.5536,47.2184"  # Nantes (near the accessible accommodation)

        response = self.client.get(reverse("accommodation-list"), {"center": center, "radius": 0.2})
        results = response.json()

        assert len(results["results"]["features"]) == 1

        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert self.accommodation_nantes_accessible_w_coliving_cheap.id in returned_ids
        assert self.accommodation_nantes_non_accessible_expensive.id not in returned_ids

        response = self.client.get(reverse("accommodation-list"), {"center": center, "radius": 2})
        results = response.json()

        assert len(results["results"]["features"]) == 2

        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert self.accommodation_nantes_accessible_w_coliving_cheap.id in returned_ids
        assert self.accommodation_nantes_non_accessible_expensive.id in returned_ids

        center_paris = "2.35,48.85"  # Paris

        response = self.client.get(reverse("accommodation-list"), {"center": center_paris, "radius": 10})
        results = response.json()

        assert len(results["results"]["features"]) == 1

        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert self.accommodation_paris.id in returned_ids
        assert self.accommodation_lyon.id not in returned_ids
        assert self.accommodation_nantes_accessible_w_coliving_cheap.id not in returned_ids
        assert self.accommodation_nantes_non_accessible_expensive.id not in returned_ids

    def test_accommodations_with_availibility_first(self):
        accommodation_without_availibity_1 = AccommodationFactory(geom=Point(2.36, 48.87), nb_t1_available=None)

        accommodation_with_availibility = AccommodationFactory(geom=Point(2.35, 48.85), nb_t1_bis_available=1)

        accommodation_without_availibity_2 = AccommodationFactory(geom=Point(2.36, 48.86), nb_t1_available=0)

        response = self.client.get(reverse("accommodation-list"))
        assert response.status_code == 200

        features = response.json()["results"]["features"]
        returned_ids = [feature["id"] for feature in features]

        assert accommodation_with_availibility.id in returned_ids
        assert accommodation_without_availibity_1.id in returned_ids
        assert accommodation_without_availibity_2.id in returned_ids

        assert returned_ids.index(accommodation_with_availibility.id) < returned_ids.index(
            accommodation_without_availibity_1.id
        )
        assert returned_ids.index(accommodation_with_availibility.id) < returned_ids.index(
            accommodation_without_availibity_2.id
        )
