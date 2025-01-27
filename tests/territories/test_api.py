from unittest import mock

from django.contrib.gis.geos import MultiPolygon, Polygon
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

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
                },
                {
                    "id": mock.ANY,
                    "name": "Marseille",
                    "bbox": None,
                    "postal_codes": ["13001", "13002"],
                    "popular": False,
                },
            ],
        )


class CityDetailAPITest(APITestCase):
    def setUp(self):
        lyon_multipolygon = MultiPolygon(
            Polygon(((4.7921, 45.7640), (4.8301, 45.7640), (4.8301, 45.7790), (4.7921, 45.7790), (4.7921, 45.7640)))
        )
        self.city = CityFactory.create(
            name="Lyon",
            slug="lyon",
            postal_codes=["69001", "69002"],
            epci_code="EPCI123",
            insee_code="12345",
            average_income=30000,
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
            insee_code="23456",
            average_income=20000,
            popular=True,
            nb_students=10000,
            boundary=saint_etienne_multipolygon,
        )

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
                "insee_code": "12345",
                "average_income": 30000,
                "popular": True,
                "bbox": {"xmax": 4.8301, "xmin": 4.7921, "ymax": 45.779, "ymin": 45.764},
                "nb_students": 60000,
                "nearby_cities": [{"name": "Saint-Etienne", "slug": "saint-etienne"}],
            },
        )

    def test_get_city_details_not_found(self):
        url = reverse("city-detail", kwargs={"slug": "unknown-city"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
