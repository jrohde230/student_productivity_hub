from django.contrib import admin

from .models import Assignment


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "assignment_name",
        "class_name",
        "subject",
        "due_date",
        "user",
        "created_at",
    )
    list_filter = ("due_date", "subject", "created_at")
    search_fields = (
        "assignment_name",
        "class_name",
        "subject",
        "assignment_url",
        "user__username",
        "user__email",
    )
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)
    date_hierarchy = "due_date"
