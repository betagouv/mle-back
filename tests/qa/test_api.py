from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tests.qa.factories import QuestionAnswerFactory
from tests.territories.factories import CityFactory


class QuestionAnswerAPITests(APITestCase):
    def setUp(self):
        self.city = CityFactory.create()
        self.content_type = ContentType.objects.get_for_model(self.city.__class__)
        self.qa = QuestionAnswerFactory.create(content_type=self.content_type, object_id=self.city.id)

    def test_list_question_answers(self):
        response = self.client.get(reverse("questionanswers-list-create"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["title_fr"], self.qa.title_fr)
