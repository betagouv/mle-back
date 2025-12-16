import base64
from unittest.mock import ANY, patch

from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accommodation.models import Accommodation
from tests.account.factories import OwnerFactory, UserFactory
from tests.territories.factories import AcademyFactory

from .factories import AccommodationFactory, ExternalSourceFactory


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
            accept_waiting_list=False,
            scholarship_holders_priority=False,
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
        assert result["accept_waiting_list"] is False
        assert result["scholarship_holders_priority"] is False

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
            nb_t1=20,
            nb_t1_available=2,
            accept_waiting_list=True,
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

        assert {
            "id": ANY,
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-1.5536, 47.2184]},
            "properties": {
                "name": self.accommodation_nantes_accessible_w_coliving_cheap.name,
                "slug": self.accommodation_nantes_accessible_w_coliving_cheap.slug,
                "city": self.accommodation_nantes_accessible_w_coliving_cheap.city,
                "postal_code": self.accommodation_nantes_accessible_w_coliving_cheap.postal_code,
                "nb_total_apartments": ANY,
                "nb_accessible_apartments": 2,
                "nb_coliving_apartments": 5,
                "price_min": 300,
                "images_urls": None,
                "available": True,
                "published": True,
                "nb_t1": 20,
                "nb_t1_available": 2,
                "nb_t1_bis": None,
                "nb_t1_bis_available": None,
                "nb_t2": None,
                "nb_t2_available": None,
                "nb_t3": None,
                "nb_t3_available": None,
                "nb_t4_more": None,
                "nb_t4_more_available": None,
                "accept_waiting_list": True,
                "scholarship_holders_priority": False,
            },
        } in results["results"]["features"]

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

        response = self.client.get(reverse("accommodation-list"), {"bbox": bbox, "only_with_availibility": True})
        results = response.json()

        assert len(results["results"]["features"]) == 1

        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert self.accommodation_nantes_accessible_w_coliving_cheap.id in returned_ids

        academy = AcademyFactory(
            name="Academie de Paris",
            boundary=MultiPolygon(Polygon(((2.34, 48.84), (2.36, 48.84), (2.36, 48.86), (2.34, 48.86), (2.34, 48.84)))),
        )
        response = self.client.get(reverse("accommodation-list"), {"academy": academy.id})
        results = response.json()
        assert len(results["results"]["features"]) == 1
        returned_ids = [feature["id"] for feature in results["results"]["features"]]
        assert self.accommodation_paris.id in returned_ids

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

    def test_accommodations_sorting_nominal(self):
        accommodation_with_availibility = AccommodationFactory(geom=Point(2.35, 48.85), nb_t1_bis_available=1)

        accommodation_with_unknown_availibity_waiting_list = AccommodationFactory(
            geom=Point(2.36, 48.87), nb_t1_available=None, accept_waiting_list=True
        )
        accommodation_with_unknown_availibity_no_waiting_list = AccommodationFactory(
            geom=Point(2.36, 48.87), nb_t1_available=None, accept_waiting_list=False
        )

        accommodation_without_availibity_waiting_list = AccommodationFactory(
            geom=Point(2.36, 48.86), nb_t1_available=0, accept_waiting_list=True
        )
        accommodation_without_availibity_no_waiting_list = AccommodationFactory(
            geom=Point(2.36, 48.86), nb_t1_available=0, accept_waiting_list=False
        )

        accommodation_with_multiple_availibilities = AccommodationFactory(
            geom=Point(2.37, 48.88),
            nb_t1_available=1,
            nb_t2_available=2,
            nb_t3_available=0,
            nb_t1_bis_available=0,
            nb_t4_more_available=0,
            accept_waiting_list=True,
        )

        accommodation_mixed_null_and_zero = AccommodationFactory(
            geom=Point(2.38, 48.89),
            nb_t1_available=None,
            nb_t2_available=0,
            nb_t3_available=None,
            nb_t1_bis_available=None,
            nb_t4_more_available=None,
            accept_waiting_list=True,
        )

        response = self.client.get(reverse("accommodation-list"))
        assert response.status_code == 200

        features = response.json()["results"]["features"]
        returned_ids = [feature["id"] for feature in features]

        assert accommodation_with_availibility.id in returned_ids
        assert accommodation_with_unknown_availibity_waiting_list.id in returned_ids
        assert accommodation_with_unknown_availibity_no_waiting_list.id in returned_ids
        assert accommodation_without_availibity_waiting_list.id in returned_ids
        assert accommodation_without_availibity_no_waiting_list.id in returned_ids

        assert returned_ids.index(accommodation_with_availibility.id) < returned_ids.index(
            accommodation_with_unknown_availibity_waiting_list.id
        )

        assert returned_ids.index(accommodation_without_availibity_waiting_list.id) < returned_ids.index(
            accommodation_with_unknown_availibity_waiting_list.id
        )

        assert returned_ids.index(accommodation_with_unknown_availibity_waiting_list.id) < returned_ids.index(
            accommodation_with_unknown_availibity_no_waiting_list.id
        )
        assert returned_ids.index(accommodation_with_unknown_availibity_no_waiting_list.id) < returned_ids.index(
            accommodation_without_availibity_no_waiting_list.id
        )

        assert returned_ids.index(accommodation_with_multiple_availibilities.id) < returned_ids.index(
            accommodation_with_availibility.id
        )

        assert returned_ids.index(accommodation_mixed_null_and_zero.id) < returned_ids.index(
            accommodation_with_unknown_availibity_waiting_list.id
        )

    def test_accommodation_list_crous(self):
        accommodation_crous = AccommodationFactory(geom=Point(2.35, 48.85))
        ExternalSourceFactory(accommodation=accommodation_crous, source="crous")

        response = self.client.get(reverse("accommodation-list"))

        assert response.status_code == 200
        results = response.json()

        features = response.json()["results"]["features"]
        returned_ids = [feature["id"] for feature in features]

        assert results["count"] == 6
        assert accommodation_crous.id not in returned_ids

        response = self.client.get(reverse("accommodation-list"), {"view_crous": True})

        assert response.status_code == 200
        results = response.json()

        features = response.json()["results"]["features"]
        returned_ids = [feature["id"] for feature in features]

        assert results["count"] == 1
        assert returned_ids == [accommodation_crous.id]


class MyAccommodationListAPITests(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.owner = OwnerFactory(users=[self.user])
        self.client.force_authenticate(user=self.user)

        self.other_owner = OwnerFactory()

        self.my_accommodation_1 = AccommodationFactory(
            owner=self.owner,
            geom=Point(2.35, 48.85),
            published=True,
            name="Paris Residence",
            nb_t2_available=2,
        )
        self.my_accommodation_2 = AccommodationFactory(
            owner=self.owner,
            geom=Point(4.85, 45.75),
            published=True,
            name="Lyon Coliving",
            nb_t1_available=0,
            nb_t2_available=0,
            nb_t3_available=0,
            nb_t4_more_available=0,
        )

        self.other_accommodation = AccommodationFactory(
            owner=self.other_owner,
            geom=Point(-1.55, 47.21),
            published=True,
            name="Nantes Loft",
        )

    def test_my_accommodation_list_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("my-accommodation-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_my_accommodation_list_returns_only_user_accommodations(self):
        response = self.client.get(reverse("my-accommodation-list"))
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        results = data["results"]["features"]

        returned_ids = [feature["id"] for feature in results]

        assert len(results) == 2
        assert self.my_accommodation_1.id in returned_ids
        assert self.my_accommodation_2.id in returned_ids
        assert self.other_accommodation.id not in returned_ids

    def test_my_accommodation_list_empty_if_no_owned(self):
        other_user = UserFactory()
        self.client.force_authenticate(user=other_user)

        response = self.client.get(reverse("my-accommodation-list"))
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["count"] == 0
        assert len(data["results"]["features"]) == 0

    def test_my_accommodation_list_search_by_name(self):
        url = reverse("my-accommodation-list") + "?search=paris"
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        results = data["results"]["features"]
        names = [r["properties"]["name"].lower() for r in results]

        assert len(results) == 1
        assert "paris" in names[0]

    def test_my_accommodation_list_filter_has_availability_true(self):
        url = reverse("my-accommodation-list") + "?has_availability=true"
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        results = data["results"]["features"]
        slugs = [r["properties"]["slug"] for r in results]

        assert self.my_accommodation_1.slug in slugs
        assert self.my_accommodation_2.slug not in slugs


class MyAccommodationDetailAPITests(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.owner = OwnerFactory(users=[self.user])
        self.client.force_authenticate(user=self.user)

        self.other_owner = OwnerFactory()

        self.my_accommodation = AccommodationFactory(
            owner=self.owner,
            slug="my-accommodation",
            geom=Point(2.35, 48.85),
            published=True,
            name="My First Accommodation",
        )

        self.other_accommodation = AccommodationFactory(
            owner=self.other_owner,
            slug="not-mine",
            geom=Point(2.35, 48.85),
            published=True,
            name="Someone Else's Accommodation",
        )

    def test_create_new_accommodation(self):
        url = reverse("my-accommodation-list")
        payload = {
            "name": "New Accommodation",
            "address": "123 Rue de Paris",
            "city": "Paris",
            "postal_code": "75001",
            "geom": {"type": "Point", "coordinates": [2.35, 48.85]},
            "published": True,
        }

        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.content

        data = response.json()["properties"]
        assert data["name"] == "New Accommodation"
        assert "slug" in data

        acc = Accommodation.objects.get(name="New Accommodation")
        assert acc.owner == self.owner

    def test_get_my_accommodation(self):
        url = reverse("my-accommodation-detail", args=[self.my_accommodation.slug])

        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()["properties"]
        assert data["name"] == self.my_accommodation.name
        assert data["updated_at"] is not None

    def test_post_requires_authentication(self):
        self.client.force_authenticate(user=None)
        url = reverse("my-accommodation-list")
        response = self.client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_patch_update_own_accommodation(self):
        url = reverse("my-accommodation-detail", args=[self.my_accommodation.slug])

        current_slug = self.my_accommodation.slug

        payload = {
            "name": "Updated Accommodation Name",
            "bathroom": "private",
            "laundry_room": True,
            "slug": "new_slug",
            "nb_t1": 104,
            "nb_t1_available": 10,
            "nb_t2": 16,
            "price_min_t1": 300,
            "price_max_t1": 450,
        }

        response = self.client.patch(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()["properties"]
        assert data["name"] == "Updated Accommodation Name"
        assert data["bathroom"] == "private"
        assert data["laundry_room"] is True
        assert data["updated_at"] is not None
        assert data["slug"] == current_slug, "slug should not be changed"
        assert data["nb_t1"] == 104
        assert data["nb_t2"] == 16
        assert data["nb_t3"] is None
        assert data["nb_t1_available"] == 10
        assert data["price_min_t1"] == 300
        assert data["price_max_t1"] == 450

        self.my_accommodation.refresh_from_db()
        assert self.my_accommodation.name == "Updated Accommodation Name"
        assert self.my_accommodation.nb_total_apartments == 120
        assert self.my_accommodation.published is True

        payload = {"published": False}

        response = self.client.patch(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK

        self.my_accommodation.refresh_from_db()
        assert self.my_accommodation.published is False

    def test_patch_cannot_update_others_accommodation(self):
        url = reverse("my-accommodation-detail", args=[self.other_accommodation.slug])

        payload = {"name": "Hack attempt!"}

        response = self.client.patch(url, payload, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_patch_requires_authentication(self):
        self.client.force_authenticate(user=None)
        url = reverse("my-accommodation-detail", args=[self.my_accommodation.slug])
        response = self.client.patch(url, {"name": "Should Fail"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_patch_cannot_change_id_or_slug(self):
        url = reverse("my-accommodation-detail", args=[self.my_accommodation.slug])

        original_id = self.my_accommodation.id
        original_slug = self.my_accommodation.slug

        payload = {"id": 9999, "slug": "hacked-slug", "name": "Updated Name With Read-Only Fields"}

        response = self.client.patch(url, payload, format="json")
        assert response.status_code == 200

        self.my_accommodation.refresh_from_db()

        assert self.my_accommodation.id == original_id
        assert self.my_accommodation.slug == original_slug

        assert self.my_accommodation.name == "Updated Name With Read-Only Fields"

        data = response.json()["properties"]
        assert data["slug"] == original_slug
        assert data["name"] == "Updated Name With Read-Only Fields"

    def test_patch_updates_images_in_correct_order(self):
        url = reverse("my-accommodation-detail", args=[self.my_accommodation.slug])

        new_urls = [
            "https://s3.fake/image_b.jpg",
            "https://s3.fake/image_a.jpg",
            "https://s3.fake/image_c.jpg",
        ]

        response = self.client.patch(url, {"images_urls": new_urls}, format="json")
        assert response.status_code == status.HTTP_200_OK

        self.my_accommodation.refresh_from_db()
        assert self.my_accommodation.images_urls == new_urls, "URLs should be stored preserved order"

    def test_create_accommodation_returns_400_if_nb_available_exceeds_total(self):
        url = reverse("my-accommodation-list")
        payload = {
            "name": "Invalid Accommodation",
            "address": "123 Rue de Paris",
            "city": "Paris",
            "postal_code": "75001",
            "geom": {"type": "Point", "coordinates": [2.35, 48.85]},
            "nb_t1": 2,
            "nb_t1_available": 5,
            "published": True,
        }

        response = self.client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.content
        assert "nb_t1_available" in response.json()

    def test_patch_returns_400_if_nb_available_exceeds_total(self):
        url = reverse("my-accommodation-detail", args=[self.my_accommodation.slug])

        payload = {
            "nb_t2": 1,
            "nb_t2_available": 3,
        }

        response = self.client.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.content
        assert "nb_t2_available" in response.json()


class MyAccommodationImageUploadTests(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.owner = OwnerFactory(users=[self.user])
        self.client.force_authenticate(user=self.user)

        self.accommodation = AccommodationFactory(
            owner=self.owner,
            slug="my-place",
            images_urls=[],
        )

        self.url = reverse("my-accommodation-upload", args=[self.accommodation.slug])

    @patch("accommodation.views.upload_image_to_s3")
    def test_upload_multiple_images_success(self, mock_upload):
        mock_upload.side_effect = lambda data: f"https://s3.fake/{len(data)}.jpg"

        file1 = SimpleUploadedFile("photo1.jpg", b"dummydata1", content_type="image/jpeg")
        file2 = SimpleUploadedFile("photo2.png", b"dummydata2", content_type="image/png")

        response = self.client.post(self.url, {"images": [file1, file2]}, format="multipart")

        assert response.status_code == status.HTTP_201_CREATED
        urls = response.data["images_urls"]
        assert len(urls) == 2
        assert all(url.startswith("https://s3.fake/") for url in urls)
        assert mock_upload.call_count == 2

        self.accommodation.refresh_from_db()
        assert self.accommodation.images_urls == []

    @patch("accommodation.views.upload_image_to_s3")
    def test_upload_requires_ownership(self, mock_upload):
        other_user = UserFactory()
        self.client.force_authenticate(user=other_user)

        file1 = SimpleUploadedFile("photo1.jpg", b"dummydata1", content_type="image/jpeg")
        response = self.client.post(self.url, {"images": [file1]}, format="multipart")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        mock_upload.assert_not_called()

    def test_upload_requires_file(self):
        response = self.client.post(self.url, {}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No files provided" in response.data["detail"]


class FavoriteAccommodationViewSetTests(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

        self.accommodation = AccommodationFactory(
            slug="my-favorite-accommodation",
            geom=Point(2.35, 48.85),
            published=True,
            name="My Favorite Accommodation",
        )

    def test_create_favorite_accommodation(self):
        url = reverse("favorite-accommodation-list")
        payload = {"accommodation_slug": self.accommodation.slug}

        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_list_favorite_accommodations(self):
        url = reverse("favorite-accommodation-list")
        payload = {"accommodation_slug": self.accommodation.slug}

        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        results = data["results"]

        assert len(results) == 1
        assert results[0]["accommodation"]["id"] == self.accommodation.id

    def test_delete_favorite_accommodation(self):
        url = reverse("favorite-accommodation-list")
        payload = {"accommodation_slug": self.accommodation.slug}

        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        url = reverse("favorite-accommodation-detail", args=[self.accommodation.slug])

        response = self.client.delete(url, format="json")
        assert response.status_code == status.HTTP_204_NO_CONTENT
