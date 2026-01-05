import factory
from alerts.models import AccommodationAlert
from tests.account.factories import StudentFactory
from tests.territories.factories import CityFactory, DepartmentFactory, AcademyFactory


class AccommodationAlertFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AccommodationAlert

    class Params:
        with_city = factory.Trait(city=factory.SubFactory(CityFactory))
        with_department = factory.Trait(department=factory.SubFactory(DepartmentFactory))
        with_academy = factory.Trait(academy=factory.SubFactory(AcademyFactory))

    name = factory.Faker("name")
    student = factory.SubFactory(StudentFactory)
    has_coliving = factory.Faker("boolean")
    is_accessible = factory.Faker("boolean")
    max_price = factory.Faker("random_int", min=300, max=1500)
