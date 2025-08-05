import factory
import factory.fuzzy
from django.contrib.gis.geos import Point

from institution.models import EducationalInstitution
from tests.territories.factories import AcademyFactory


class EducationalInstitutionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EducationalInstitution

    name = factory.Faker("company")
    geom = factory.LazyFunction(lambda: Point(2.35, 48.85))
    address = factory.Faker("address")
    city = factory.Faker("city")
    postal_code = factory.Faker("postcode")
    academy = factory.SubFactory(AcademyFactory)
