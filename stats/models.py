from django.conf import settings
from django.db import models
from django.utils import timezone


class Stats(models.Model):
    """Model to store website statistics from Matomo API"""
    
    PERIOD_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    # Metadata
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    date_from = models.DateField()
    date_to = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)
    
    # Visiteurs uniques
    unique_visitors = models.IntegerField()
    
    # Nouvelles visites (en %)
    new_visits_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Durée moyenne (in seconds)
    average_duration = models.IntegerField()
    
    # Evolution (%) - for unique visitors
    visitors_evolution_percentage = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Taux de rebond (%)
    bounce_rate_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Evolution (%) - for bounce rate
    bounce_rate_evolution_percentage = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Pages vues
    page_views = models.IntegerField()
    
    # Nombre de visiteurs par pages
    visitors_per_page = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Evolution (%) - for page views
    page_views_evolution_percentage = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Top 3 des pages les + vues (JSON field)
    top_pages = models.JSONField(default=list)
    
    # Principales pages d'entrées (JSON field)
    main_entry_pages = models.JSONField(default=list)
    
    # Sources principales (JSON field)
    main_sources = models.JSONField(default=list)
    
    class Meta:
        verbose_name = "Website Statistics"
        verbose_name_plural = "Website Statistics"
        ordering = ['-date_from']
        indexes = [
            models.Index(fields=['period', 'date_from']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_period_display()} stats - {self.date_from} to {self.date_to}"


class EventStats(models.Model):
    """Stores Matomo custom event statistics"""

    PERIOD_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    date_from = models.DateField()
    date_to = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)

    category = models.CharField(max_length=100)
    action = models.CharField(max_length=200)
    nb_events = models.IntegerField(default=0)
    nb_unique_events = models.IntegerField(default=0)
    event_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Event Statistics"
        verbose_name_plural = "Event Statistics"
        ordering = ['-date_from', '-nb_events']
        indexes = [
            models.Index(fields=['period', 'date_from']),
            models.Index(fields=['category', 'action']),
        ]

    def __str__(self):
        return f"{self.category} > {self.action} ({self.nb_events}) - {self.date_from}"


class GestionnaireLoginEvent(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="login_events",
    )
    owner = models.ForeignKey(
        "account.Owner",
        on_delete=models.SET_NULL,
        null=True,
        related_name="login_events",
    )
    logged_in_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-logged_in_at"]
        indexes = [
            models.Index(fields=["owner", "-logged_in_at"]),
            models.Index(fields=["user", "-logged_in_at"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.logged_in_at}"


class AccommodationChangeLog(models.Model):
    ACTION_CHOICES = [
        ("created", "Created"),
        ("updated", "Updated"),
    ]

    accommodation = models.ForeignKey(
        "accommodation.Accommodation",
        on_delete=models.CASCADE,
        related_name="change_logs",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="accommodation_change_logs",
    )
    owner = models.ForeignKey(
        "account.Owner",
        on_delete=models.SET_NULL,
        null=True,
        related_name="accommodation_change_logs",
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    data_diff = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "-created_at"]),
            models.Index(fields=["accommodation", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.action} - {self.accommodation} - {self.created_at}"
