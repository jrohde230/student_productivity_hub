from django.contrib import admin

from .models import CalendarEvent


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "event_date", "link", "created_at")
    list_filter = ("event_date", "created_at")
    search_fields = ("title", "link", "user__username", "user__email")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)
    date_hierarchy = "event_date"
