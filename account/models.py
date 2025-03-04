from autoslug import AutoSlugField
from django.contrib.auth.models import Group, User
from django.contrib.gis.db import models
from django.db import transaction


class Owner(models.Model):
    name = models.CharField(max_length=200)
    slug = AutoSlugField(max_length=255, default="", unique=True, populate_from="name")
    url = models.URLField(max_length=500, blank=True, null=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="owner")
    image = models.BinaryField(null=True, blank=True)

    def __str__(self):
        return self.name

    @classmethod
    def create(cls, data):
        if not data:
            return

        with transaction.atomic():
            owner, created = cls.objects.get_or_create(name=data.get("name"), url=data.get("url"))

            if not created:
                return owner

            user = User.objects.create_user(username=owner.name, password=None, is_active=False, is_staff=True)
            owner.user = user
            owner.save()

            owners_group = Group.objects.get(name="Owners")
            user.groups.add(owners_group)
            user.save()

            return owner
