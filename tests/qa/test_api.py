from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tests.qa.factories import QuestionAnswerFactory
from tests.territories.factories import CityFactory


class QuestionAnswerAPITests(APITestCase):
    def setUp(self):
        self.city = CityFactory(name="Lyon")
        self.qa1 = QuestionAnswerFactory(content_type=self.city.get_content_type(), object_id=self.city.id)
        self.qa2 = QuestionAnswerFactory(content_type=self.city.get_content_type(), object_id=self.city.id)

    def test_list_question_answers_by_territory(self):
        response = self.client.get(
            reverse("questionanswers-by-territory"), {"content_type": "city", "object_id": self.city.id}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0]["title_fr"], self.qa1.title_fr)

    def test_missing_content_type(self):
        response = self.client.get(reverse("questionanswers-by-territory"), {"object_id": self.city.id})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["detail"], "Both 'content_type' and 'object_id' parameters are required.")

    def test_missing_object_id(self):
        response = self.client.get(reverse("questionanswers-by-territory"), {"content_type": "city"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["detail"], "Both 'content_type' and 'object_id' parameters are required.")

    def test_invalid_content_type(self):
        response = self.client.get(
            reverse("questionanswers-by-territory"), {"content_type": "invalid_type", "object_id": self.city.id}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["detail"], "Invalid content_type: invalid_type")
