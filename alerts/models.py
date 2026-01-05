from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy

from account.models import Student
from territories.models import Academy, City, Department


class AccommodationAlert(models.Model):
    name = models.CharField(max_length=255, verbose_name=gettext_lazy("Name"))
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="accommodation_alerts")
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accommodation_alerts",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accommodation_alerts",
    )
    academy = models.ForeignKey(
        Academy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accommodation_alerts",
    )
    has_coliving = models.BooleanField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=gettext_lazy("Has coliving"),
    )
    is_accessible = models.BooleanField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=gettext_lazy("Accessible for disabled people"),
    )
    max_price = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=gettext_lazy("Maximum price"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    receive_notifications = models.BooleanField(default=True, verbose_name=gettext_lazy("Receive notifications"))

    class Meta:
        verbose_name = gettext_lazy("Accommodation alert")
        verbose_name_plural = gettext_lazy("Accommodation alerts")

    def __str__(self):
        localisation = self.city or self.department or self.academy
        return f"{self.student} - {localisation} - {self.has_coliving} - {self.is_accessible} - {self.max_price}"
