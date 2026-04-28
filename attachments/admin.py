from django.contrib import admin

from .models import Attachment


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "original_name",
        "user",
        "content_type",
        "object_id",
        "target",
        "file",
        "created_at",
    )
    list_filter = ("content_type", "created_at")
    search_fields = ("original_name", "user__username", "user__email")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)

    @admin.display(description="Target")
    def target(self, obj):
        try:
            return str(obj.content_object)
        except Exception:
            return "—"
