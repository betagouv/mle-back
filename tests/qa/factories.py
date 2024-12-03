import factory
from django.contrib.contenttypes.models import ContentType

from qa.models import QuestionAnswer
from tests.territories.factories import CityFactory


class QuestionAnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = QuestionAnswer

    title_fr = factory.Faker("sentence", nb_words=5)
    title_en = factory.Faker("sentence", nb_words=5)
    content_fr = factory.Faker("text")
    content_en = factory.Faker("text")

    content_type = factory.LazyAttribute(lambda obj: ContentType.objects.get_for_model(CityFactory._meta.model))
    object_id = factory.SubFactory(CityFactory)
