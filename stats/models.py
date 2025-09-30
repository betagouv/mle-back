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
