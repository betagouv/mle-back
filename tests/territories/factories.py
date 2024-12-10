import factory

from territories.models import Academy, City, Department


class AcademyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Academy

    name = factory.Faker("company")
    boundary = None


class DepartmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Department

    name = factory.Faker("city")
    code = factory.Faker("random_number", digits=2)
    academy = factory.SubFactory(AcademyFactory)
    boundary = None


class CityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = City

    name = factory.Faker("city")
    postal_codes = factory.List(["75000", "75001"])
    department = factory.SubFactory(DepartmentFactory)
    boundary = None
