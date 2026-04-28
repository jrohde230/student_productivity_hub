from django.contrib import admin

from .models import Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("label", "user", "content_type", "object_id", "target", "created_at")
    list_filter = ("content_type", "created_at")
    search_fields = ("label", "user__username", "user__email")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)

    @admin.display(description="Target")
    def target(self, obj):
        try:
            return str(obj.content_object)
        except Exception:
            return "—"
