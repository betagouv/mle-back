from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework.test import APITestCase

from .factories import EducationalInstitutionFactory


class EducationalInstitutionListAPITests(APITestCase):
    def setUp(self):
        self.institution_paris = EducationalInstitutionFactory(geom=Point(2.35, 48.85))
        self.institution_lyon = EducationalInstitutionFactory(geom=Point(4.85, 45.75))
        self.institution_no_geom = EducationalInstitutionFactory(geom=None)

    def test_list_base(self):
        url = reverse("institution-list")
        response = self.client.get(url)
        assert response.status_code == 200

        features = response.json()["results"]["features"]
        ids = [f["id"] for f in features]

        assert self.institution_paris.id in ids
        assert self.institution_lyon.id in ids
        assert self.institution_no_geom.id not in ids

    def test_filter_bbox(self):
        url = reverse("institution-list")
        bbox = "4.80,45.70,4.90,45.80"  # lyon only
        response = self.client.get(url, {"bbox": bbox})

        features = response.json()["results"]["features"]
        ids = [f["id"] for f in features]

        assert self.institution_paris.id not in ids
        assert self.institution_lyon.id in ids
