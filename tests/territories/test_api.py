from unittest import mock
from unittest.mock import patch
import sib_api_v3_sdk

from django.contrib.gis.geos import MultiPolygon, Polygon
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from territories.models import Academy, City, Department
from tests.accommodation.factories import AccommodationFactory
from tests.territories.factories import AcademyFactory, CityFactory, DepartmentFactory


class TerritoryCombinedListAPITests(APITestCase):
    def setUp(self):
        multi_polygon = MultiPolygon(Polygon(((5, 5), (5, 10), (10, 10), (10, 5), (5, 5))))
        self.academy = AcademyFactory.create(name="Academie du Rhône", boundary=multi_polygon)
        self.academy_paris = AcademyFactory.create(
            name="Académie de Paris", boundary=MultiPolygon(Polygon(((2, 48), (2, 49), (3, 49), (3, 48), (2, 48))))
        )
        self.department = DepartmentFactory.create(name="Rhône", code=69, academy=self.academy, boundary=multi_polygon)
        self.city = CityFactory.create(
            name="Lyon", postal_codes=["69001", "69002", "69003"], department=self.department, average_income=30000
        )
        AccommodationFactory.create(city=self.city.name, postal_code="69001", nb_total_apartments=12)

    def test_get_territory_combined_list_filtered(self):
        for search_term in ("rh", "rhone", "rhône", "Rhône"):
            response = self.client.get(reverse("territory-combined-list") + f"?q={search_term}")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.assertEqual(
                response.json(),
                {
                    "academies": [
                        {
                            "id": mock.ANY,
                            "name": "Academie du Rhône",
                            "bbox": {
                                "xmin": 5.0,
                                "ymin": 5.0,
                                "xmax": 10.0,
                                "ymax": 10.0,
                            },
                        }
                    ],
                    "departments": [
                        {
                            "id": mock.ANY,
                            "name": "Rhône",
                            "code": "69",
                            "bbox": {
                                "xmin": 5.0,
                                "ymin": 5.0,
                                "xmax": 10.0,
                                "ymax": 10.0,
                            },
                        }
                    ],
                    "cities": [],
                },
            )

    def test_get_academies_list(self):
        response = self.client.get(reverse("academies-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.json(),
            [
                {
                    "id": mock.ANY,
                    "name": "Académie de Paris",
                    "bbox": {
                        "xmin": 2.0,
                        "ymin": 48.0,
                        "xmax": 3.0,
                        "ymax": 49.0,
                    },
                },
                {
                    "id": mock.ANY,
                    "name": "Academie du Rhône",
                    "bbox": {
                        "xmin": 5.0,
                        "ymin": 5.0,
                        "xmax": 10.0,
                        "ymax": 10.0,
                    },
                },
            ],
        )

    def test_get_departments_list(self):
        response = self.client.get(reverse("departments-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.json(),
            [
                {
                    "id": mock.ANY,
                    "name": "Rhône",
                    "code": "69",
                    "bbox": {"xmin": 5.0, "ymin": 5.0, "xmax": 10.0, "ymax": 10.0},
                }
            ],
        )

    def test_get_cities_list(self):
        response = self.client.get(reverse("cities-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.json(),
            [
                {
                    "id": mock.ANY,
                    "name": "Lyon",
                    "popular": False,
                    "bbox": None,
                    "postal_codes": ["69001", "69002", "69003"],
                    "nb_apartments": 12,
                }
            ],
        )

        response = self.client.get(reverse("cities-list") + "?department=69")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.json(),
            [
                {
                    "id": mock.ANY,
                    "name": "Lyon",
                    "popular": False,
                    "bbox": None,
                    "postal_codes": ["69001", "69002", "69003"],
                    "nb_apartments": 12,
                }
            ],
        )

        response = self.client.get(reverse("cities-list") + "?department=38")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json(), [])

        CityFactory.create(
            name="Paris",
            postal_codes=["75001", "75002"],
            department=self.department,
            popular=True,
            average_income=40000,
        )
        CityFactory.create(
            name="Marseille",
            postal_codes=["13001", "13002"],
            department=self.department,
            popular=False,
            average_income=25000,
        )

        response = self.client.get(reverse("cities-list") + "?popular=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.json(),
            [
                {
                    "id": mock.ANY,
                    "name": "Paris",
                    "bbox": None,
                    "postal_codes": ["75001", "75002"],
                    "popular": True,
                    "nb_apartments": 0,
                }
            ],
        )

        response = self.client.get(reverse("cities-list") + "?popular=false")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.json(),
            [
                {
                    "id": mock.ANY,
                    "name": "Lyon",
                    "bbox": None,
                    "postal_codes": ["69001", "69002", "69003"],
                    "popular": False,
                    "nb_apartments": 12,
                },
                {
                    "id": mock.ANY,
                    "name": "Marseille",
                    "bbox": None,
                    "postal_codes": ["13001", "13002"],
                    "popular": False,
                    "nb_apartments": 0,
                },
            ],
        )


class CityDetailAPITest(APITestCase):
    maxDiff = None

    def setUp(self):
        lyon_multipolygon = MultiPolygon(
            Polygon(((4.7921, 45.7640), (4.8301, 45.7640), (4.8301, 45.7790), (4.7921, 45.7790), (4.7921, 45.7640)))
        )
        self.city = CityFactory.create(
            name="Lyon",
            slug="lyon",
            postal_codes=["69001", "69002"],
            epci_code="EPCI123",
            insee_codes=[
                "69123",
                "69124",
                "69125",
                "69126",
                "69127",
                "69128",
                "69129",
                "69130",
                "69131",
                "69381",
                "69382",
                "69383",
                "69384",
                "69385",
                "69386",
                "69387",
                "69388",
                "69389",
            ],
            average_income=30000,
            average_rent=17.3,
            popular=True,
            nb_students=60000,
            boundary=lyon_multipolygon,
        )

        saint_etienne_multipolygon = MultiPolygon(
            Polygon(((4.3801, 45.4300), (4.4101, 45.4300), (4.4101, 45.4600), (4.3801, 45.4600), (4.3801, 45.4300)))
        )
        CityFactory.create(
            name="Saint-Etienne",
            slug="saint-etienne",
            postal_codes=["42000", "42100"],
            epci_code="EPCI234",
            insee_codes=["23456"],
            average_income=20000,
            popular=True,
            nb_students=10000,
            boundary=saint_etienne_multipolygon,
        )

        AccommodationFactory.create(city=self.city.name, postal_code="69001", nb_total_apartments=3)
        AccommodationFactory.create(city=self.city.name, postal_code="69001", nb_total_apartments=12)

    def test_get_city_details(self):
        url = reverse("city-detail", kwargs={"slug": self.city.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "id": mock.ANY,
                "name": "Lyon",
                "postal_codes": ["69001", "69002"],
                "epci_code": "EPCI123",
                "insee_codes": [
                    "69123",
                    "69124",
                    "69125",
                    "69126",
                    "69127",
                    "69128",
                    "69129",
                    "69130",
                    "69131",
                    "69381",
                    "69382",
                    "69383",
                    "69384",
                    "69385",
                    "69386",
                    "69387",
                    "69388",
                    "69389",
                ],
                "average_income": 30000,
                "average_rent": 17.3,
                "popular": True,
                "bbox": {"xmax": 4.8301, "xmin": 4.7921, "ymax": 45.779, "ymin": 45.764},
                "nb_students": 60000,
                "nb_apartments": 15,
                "nearby_cities": [{"name": "Saint-Etienne", "slug": "saint-etienne"}],
            },
        )

    def test_get_city_details_not_found(self):
        url = reverse("city-detail", kwargs={"slug": "unknown-city"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class NewsletterSubscriptionAPITest(APITestCase):
    def setUp(self):
        self.academy = Academy.objects.create(name="Academie de Lyon")
        self.department = Department.objects.create(name="Rhône", code="69", academy=self.academy)
        self.city = City.objects.create(name="Lyon", department=self.department, postal_codes=["69001"])
        self.url = reverse("newsletter-subscription")

    @patch("sib_api_v3_sdk.ContactsApi.get_contact_info")
    @patch("sib_api_v3_sdk.ContactsApi.update_contact")
    @patch("sib_api_v3_sdk.ContactsApi.create_contact")
    def test_successful_subscription(self, mock_create, mock_update, mock_get_info):
        error_404 = sib_api_v3_sdk.rest.ApiException(status=404, reason="Contact not found")
        mock_get_info.side_effect = error_404
        data = {"email": "test@example.com", "territory_type": "city", "territory_name": "Lyon"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["message"], "Subscription successful")
        mock_get_info.assert_called_once_with("test@example.com")

        expected_data = {
            "email": "test@example.com",
            "attributes": {
                "TERRITORY_NAME": "Lyon",
                "TERRITORY_TYPE": "city",
            },
            "listIds": [1],
            "updateEnabled": True,
        }
        mock_create.assert_called_once_with(expected_data)
        mock_update.assert_not_called()

        mock_get_info.reset_mock()
        mock_create.reset_mock()
        mock_update.reset_mock()

        mock_get_info.side_effect = None
        response = self.client.post(self.url, data, format="json")
        del expected_data["email"]
        mock_update.assert_called_once_with("test@example.com", expected_data)
        mock_create.assert_not_called()

    def test_subscription_invalid_territory(self):
        data = {"email": "test@example.com", "territory_type": "city", "territory_name": "Unknown City"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_subscription_missing_fields(self):
        data = {"email": "test@example.com", "territory_type": "city"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
