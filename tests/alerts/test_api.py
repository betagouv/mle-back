from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from alerts.models import AccommodationAlert
from tests.account.factories import StudentFactory
from tests.alerts.factories import AccommodationAlertFactory
from tests.accommodation.factories import AccommodationFactory
from tests.territories.factories import DepartmentFactory, CityFactory, AcademyFactory


class AccommodationAlertAPITests(APITestCase):
    def setUp(self):
        self.student = StudentFactory()
        self.department = DepartmentFactory.create(name="Rhône", code=69)
        self.city = CityFactory.create(
            name="Lyon", postal_codes=["69001", "69002", "69003"], department=self.department, average_income=30000
        )
        self.client.force_authenticate(user=self.student.user)

    def test_list_accommodation_alerts(self):
        AccommodationAlertFactory.create_batch(5, student=self.student, city=self.city)
        # Create an alert for another student
        AccommodationAlertFactory(city=self.city)
        response = self.client.get(reverse("accommodation-alert-list"))
        data = response.json()["results"]
        assert response.status_code == 200
        assert len(data) == 5
        for alert in data:
            assert alert["city"]["id"] == self.city.id
            assert alert["city"]["name"] == self.city.name
            assert alert["count"] == 0

    def test_create_accommodation_alert(self):
        url = reverse("accommodation-alert-list")
        payload = {
            "name": "Test Alert",
            "city_id": self.city.id,
            "has_coliving": True,
            "is_accessible": True,
            "max_price": 1500,
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Alert"
        assert data["city"]["id"] == self.city.id
        assert data["city"]["name"] == self.city.name
        assert data["has_coliving"] is True
        assert data["is_accessible"] is True
        assert data["max_price"] == 1500
        assert data["count"] == 0

    def test_update_accommodation_alert(self):
        alert = AccommodationAlertFactory(city=self.city, student=self.student)
        url = reverse("accommodation-alert-detail", args=[alert.id])
        payload = {
            "name": "Updated Alert",
            "city_id": self.city.id,
            "has_coliving": False,
            "is_accessible": False,
            "max_price": 1000,
        }
        response = self.client.put(url, payload, format="json")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Alert"
        assert data["city"]["id"] == self.city.id
        assert data["city"]["name"] == self.city.name
        assert data["has_coliving"] is False
        assert data["is_accessible"] is False
        assert data["max_price"] == 1000
        assert data["count"] == 0

    def test_delete_accommodation_alert(self):
        alert = AccommodationAlertFactory(city=self.city, student=self.student)
        url = reverse("accommodation-alert-detail", args=[alert.id])
        response = self.client.delete(url)
        assert response.status_code == 204
        assert AccommodationAlert.objects.count() == 0

    def test_retrieve_accommodation_alert(self):
        alert = AccommodationAlertFactory(city=self.city, student=self.student, name="My Alert")
        url = reverse("accommodation-alert-detail", args=[alert.id])
        response = self.client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == alert.id
        assert data["name"] == "My Alert"
        assert data["city"]["id"] == self.city.id
        assert data["city"]["name"] == self.city.name
        assert data["count"] == 0

    def test_unauthenticated_access_list(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("accommodation-alert-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_access_create(self):
        self.client.force_authenticate(user=None)
        url = reverse("accommodation-alert-list")
        payload = {"name": "Test Alert", "city_id": self.city.id}
        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_access_retrieve(self):
        alert = AccommodationAlertFactory(city=self.city, student=self.student)
        self.client.force_authenticate(user=None)
        url = reverse("accommodation-alert-detail", args=[alert.id])
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_access_update(self):
        alert = AccommodationAlertFactory(city=self.city, student=self.student)
        self.client.force_authenticate(user=None)
        url = reverse("accommodation-alert-detail", args=[alert.id])
        payload = {"name": "Updated Alert", "city_id": self.city.id}
        response = self.client.put(url, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_access_delete(self):
        alert = AccommodationAlertFactory(city=self.city, student=self.student)
        self.client.force_authenticate(user=None)
        url = reverse("accommodation-alert-detail", args=[alert.id])
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cannot_retrieve_other_student_alert(self):
        other_student = StudentFactory()
        alert = AccommodationAlertFactory(city=self.city, student=other_student)
        url = reverse("accommodation-alert-detail", args=[alert.id])
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_update_other_student_alert(self):
        other_student = StudentFactory()
        alert = AccommodationAlertFactory(city=self.city, student=other_student)
        url = reverse("accommodation-alert-detail", args=[alert.id])
        payload = {"name": "Updated Alert", "city_id": self.city.id}
        response = self.client.put(url, payload, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_delete_other_student_alert(self):
        other_student = StudentFactory()
        alert = AccommodationAlertFactory(city=self.city, student=other_student)
        url = reverse("accommodation-alert-detail", args=[alert.id])
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert AccommodationAlert.objects.count() == 1

    def test_create_alert_with_department(self):
        url = reverse("accommodation-alert-list")
        payload = {
            "name": "Department Alert",
            "department_id": self.department.id,
            "has_coliving": True,
            "max_price": 1200,
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Department Alert"
        assert data["department"]["id"] == self.department.id
        assert data["department"]["name"] == self.department.name
        assert data["department"]["code"] == str(self.department.code)
        assert data["city"] is None
        assert data["academy"] is None
        assert data["has_coliving"] is True
        assert data["max_price"] == 1200
        assert data["count"] == 0

    def test_create_alert_with_academy(self):
        academy = AcademyFactory.create(name="Académie de Lyon")
        url = reverse("accommodation-alert-list")
        payload = {
            "name": "Academy Alert",
            "academy_id": academy.id,
            "is_accessible": True,
            "max_price": 1000,
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Academy Alert"
        assert data["academy"]["id"] == academy.id
        assert data["academy"]["name"] == academy.name
        assert data["city"] is None
        assert data["department"] is None
        assert data["is_accessible"] is True
        assert data["max_price"] == 1000
        assert data["count"] == 0

    def test_get_count_accommodation_alert_by_city(self):
        alert = AccommodationAlertFactory(
            city=self.city,
            student=self.student,
            has_coliving=None,
            is_accessible=None,
            max_price=None,
        )
        AccommodationFactory.create_batch(5, city=self.city)
        response = self.client.get(reverse("accommodation-alert-detail", args=[alert.id]))
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 5

    def test_get_count_accommodation_alert_by_academy_bbox(self):
        academy_boundary = MultiPolygon(Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0))))
        academy = AcademyFactory.create(boundary=academy_boundary)
        alert = AccommodationAlertFactory(
            academy=academy,
            student=self.student,
            city=None,
            department=None,
            has_coliving=None,
            is_accessible=None,
            max_price=None,
        )
        AccommodationFactory.create(geom=Point(0.5, 0.5))
        AccommodationFactory.create(geom=Point(2, 2))
        response = self.client.get(reverse("accommodation-alert-detail", args=[alert.id]))
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1

    def test_get_count_accommodation_alert_by_city_bbox(self):
        city_boundary = MultiPolygon(Polygon(((2, 48), (2, 49), (3, 49), (3, 48), (2, 48))))
        city = CityFactory.create(boundary=city_boundary, department=self.department)
        alert = AccommodationAlertFactory(
            city=city,
            student=self.student,
            department=None,
            academy=None,
            has_coliving=None,
            is_accessible=None,
            max_price=None,
        )
        AccommodationFactory.create(geom=Point(2.5, 48.5))
        AccommodationFactory.create(geom=Point(4, 50))
        response = self.client.get(reverse("accommodation-alert-detail", args=[alert.id]))
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1

    def test_get_count_accommodation_alert_by_department_bbox(self):
        department_boundary = MultiPolygon(Polygon(((10, 10), (10, 11), (11, 11), (11, 10), (10, 10))))
        department = DepartmentFactory.create(boundary=department_boundary)
        alert = AccommodationAlertFactory(
            department=department,
            student=self.student,
            city=None,
            academy=None,
            has_coliving=None,
            is_accessible=None,
            max_price=None,
        )
        AccommodationFactory.create(geom=Point(10.5, 10.5))
        AccommodationFactory.create(geom=Point(12, 12))
        response = self.client.get(reverse("accommodation-alert-detail", args=[alert.id]))
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1

    def test_create_alert_validation_required_name(self):
        url = reverse("accommodation-alert-list")
        payload = {
            "city_id": self.city.id,
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.json()
