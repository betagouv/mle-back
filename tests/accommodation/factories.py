import random

import factory
import factory.fuzzy
from django.contrib.gis.geos import Point

from accommodation.models import Accommodation, ExternalSource


class AccommodationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Accommodation

    name = factory.Faker("company")
    geom = factory.LazyFunction(lambda: Point(2.35, 48.85))
    address = factory.Faker("address")
    city = factory.Faker("city")
    postal_code = factory.Faker("postcode")
    residence_type = factory.fuzzy.FuzzyChoice([choice[0] for choice in Accommodation.RESIDENCE_TYPE_CHOICES])
    owner_name = factory.Faker("name")
    owner_url = factory.Faker("url")
    nb_total_apartments = factory.Faker("random_int", min=10, max=100)
    published = True

    @factory.lazy_attribute
    def nb_accessible_apartments(self):
        return random.randint(1, self.nb_total_apartments - 1)


class ExternalSourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExternalSource

    accommodation = factory.SubFactory(AccommodationFactory)
    source = factory.fuzzy.FuzzyChoice([choice[0] for choice in ExternalSource.SOURCE_CHOICES])
    source_id = factory.Faker("uuid4")
