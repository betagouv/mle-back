import factory
import factory.fuzzy
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from account.models import Owner, Student
from dossier_facile.models import DossierFacileTenant

User = get_user_model()


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Group
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"group_{n}")


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


class StudentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Student

    user = factory.SubFactory(UserFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        tenant_id = kwargs.pop("dossierfacile_tenant_id", None)
        linked_at = kwargs.pop("dossierfacile_linked_at", None)
        dossier_status = kwargs.pop("dossierfacile_status", None)
        dossier_url = kwargs.pop("dossierfacile_url", None)
        dossier_pdf_url = kwargs.pop("dossierfacile_pdf_url", None)

        student = super()._create(model_class, *args, **kwargs)

        if any(value is not None for value in [tenant_id, linked_at, dossier_status, dossier_url, dossier_pdf_url]):
            tenant = DossierFacileTenant.objects.create(
                student=student,
                tenant_id=tenant_id or f"tenant-{student.pk}",
                name=student.user.get_full_name().strip() or student.user.email or student.user.username,
                status=dossier_status,
                url=dossier_url,
                pdf_url=dossier_pdf_url,
                last_synced_at=linked_at,
            )
            if linked_at:
                DossierFacileTenant.objects.filter(pk=tenant.pk).update(created_at=linked_at)

        return student
