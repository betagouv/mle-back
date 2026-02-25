from django.contrib import admin

from .models import AccommodationChangeLog, EventStats, GestionnaireLoginEvent, Stats


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


@admin.register(EventStats)
class EventStatsAdmin(admin.ModelAdmin):
    list_display = [
        'category', 'action', 'nb_events', 'nb_unique_events',
        'period', 'date_from', 'date_to', 'created_at'
    ]
    list_filter = ['period', 'category', 'date_from']
    search_fields = ['category', 'action']
    readonly_fields = ['created_at']
    date_hierarchy = 'date_from'


@admin.register(GestionnaireLoginEvent)
class GestionnaireLoginEventAdmin(admin.ModelAdmin):
    list_display = ["user", "owner", "logged_in_at"]
    list_filter = ["owner", "logged_in_at"]
    search_fields = ["user__email", "owner__name"]
    readonly_fields = ["user", "owner", "logged_in_at"]
    date_hierarchy = "logged_in_at"


@admin.register(AccommodationChangeLog)
class AccommodationChangeLogAdmin(admin.ModelAdmin):
    list_display = ["accommodation", "user", "owner", "action", "created_at"]
    list_filter = ["action", "owner", "created_at"]
    search_fields = ["accommodation__name", "user__email", "owner__name"]
    readonly_fields = ["accommodation", "user", "owner", "action", "data_diff", "created_at"]
    date_hierarchy = "created_at"
