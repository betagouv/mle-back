from django.contrib import admin
from .models import Stats


@admin.register(Stats)
class StatsAdmin(admin.ModelAdmin):
    list_display = [
        'period', 'date_from', 'date_to', 'unique_visitors', 
        'page_views', 'bounce_rate_percentage', 'created_at'
    ]
    list_filter = ['period', 'date_from', 'created_at']
    search_fields = ['date_from', 'date_to']
    readonly_fields = ['created_at']
    date_hierarchy = 'date_from'
    
    fieldsets = (
        ('Period Information', {
            'fields': ('period', 'date_from', 'date_to', 'created_at')
        }),
        ('Visitor Statistics', {
            'fields': (
                'unique_visitors', 'visitors_evolution_percentage',
                'new_visits_percentage', 'average_duration'
            )
        }),
        ('Page Statistics', {
            'fields': (
                'page_views', 'visitors_per_page', 'page_views_evolution_percentage',
                'bounce_rate_percentage', 'bounce_rate_evolution_percentage'
            )
        }),
        ('Top Content & Sources', {
            'fields': ('top_pages', 'main_entry_pages', 'main_sources'),
            'classes': ('collapse',)
        }),
    )
