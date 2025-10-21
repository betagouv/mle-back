from autoslug import AutoSlugField
from django.contrib.auth.models import Group, User
from django.contrib.gis.db import models
from django.db import transaction
from django.utils.translation import gettext_lazy


class Owner(models.Model):
    name = models.CharField(max_length=200)
    slug = AutoSlugField(max_length=255, default="", unique=True, populate_from="name")
    url = models.URLField(max_length=500, blank=True, null=True)
    users = models.ManyToManyField(User, blank=True, related_name="owners")
    image = models.BinaryField(null=True, blank=True)

    class Meta:
        verbose_name = gettext_lazy("Owner")
        verbose_name_plural = gettext_lazy("Owners")

    def __str__(self):
        return self.name

    @classmethod
    def get_or_create(cls, data):
        if not data:
            return None

        with transaction.atomic():
            owner, _ = cls.objects.get_or_create(name=data.get("name"), defaults={"url": data.get("url")})

            username = data.get("username") or owner.name

            user, created = User.objects.get_or_create(
                username=username, defaults={"is_active": False, "is_staff": True}
            )

            owner.users.add(user)

            owners_group, _ = Group.objects.get_or_create(name="Owners")
            user.groups.add(owners_group)
            user.save()

            return owner
