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
        self.department = DepartmentFactory.create(name="Rhône", academy=self.academy, boundary=multi_polygon)
        self.city = CityFactory.create(
            name="Lyon", postal_codes=["69001", "69002", "69003"], department=self.department
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
                    "name": "Academie du Rhône",
                    "bbox": {
                        "xmin": 5.0,
                        "ymin": 5.0,
                        "xmax": 10.0,
                        "ymax": 10.0,
                    },
                },
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
            ],
        )
