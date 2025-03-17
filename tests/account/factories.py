import factory
import factory.fuzzy
from django.contrib.auth import get_user_model

from account.models import Owner

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker("user_name")
    email = factory.Faker("email")


class OwnerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Owner

    name = factory.Faker("company")
    url = factory.Faker("url")
    user = factory.SubFactory(UserFactory)

    @factory.lazy_attribute
    def image(self):
        return b"fake_image_data"
