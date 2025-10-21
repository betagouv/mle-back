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
    is_staff = True
    is_active = True


class OwnerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Owner

    name = factory.Faker("company")
    url = factory.Faker("url")

    @factory.post_generation
    def users(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            # ex: OwnerFactory(users=[user1, user2])
            for user in extracted:
                self.users.add(user)
        else:
            user = UserFactory()
            self.users.add(user)

    @factory.lazy_attribute
    def image(self):
        return b"fake_image_data"
