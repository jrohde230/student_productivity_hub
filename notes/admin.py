from django.contrib import admin

from .models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "content_type",
        "object_id",
        "target",
        "body_preview",
        "created_at",
    )
    list_filter = ("content_type", "created_at")
    search_fields = ("body", "user__username", "user__email")
    readonly_fields = ("created_at", "updated_at", "content_type", "object_id")
    autocomplete_fields = ("user",)
    date_hierarchy = "created_at"

    @admin.display(description="Target")
    def target(self, obj):
        try:
            return str(obj.content_object)
        except Exception:
            return "—"

    @admin.display(description="Body")
    def body_preview(self, obj):
        t = (obj.body or "").strip().replace("\n", " ")
        return t[:60] + ("…" if len(t) > 60 else "")
