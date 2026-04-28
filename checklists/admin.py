from django.contrib import admin

from .models import ChecklistItem


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ("text", "user", "content_type", "object_id", "target", "is_done", "created_at")
    list_filter = ("is_done", "content_type", "created_at")
    search_fields = ("text", "user__username", "user__email")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)

    @admin.display(description="Target")
    def target(self, obj):
        try:
            return str(obj.content_object)
        except Exception:
            return "—"
