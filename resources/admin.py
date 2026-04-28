from django.contrib import admin

from .models import ResourceColumn, ResourceItem


class ResourceItemInline(admin.TabularInline):
    model = ResourceItem
    extra = 0
    ordering = ("sort_order",)


@admin.register(ResourceColumn)
class ResourceColumnAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "slot")
    list_filter = ("slot",)
    search_fields = ("title", "user__username", "user__email")
    autocomplete_fields = ("user",)
    inlines = (ResourceItemInline,)


@admin.register(ResourceItem)
class ResourceItemAdmin(admin.ModelAdmin):
    list_display = ("name", "column", "owner", "sort_order", "created_at")
    search_fields = ("name", "url", "column__title", "column__user__username")
    autocomplete_fields = ("column",)
    readonly_fields = ("created_at",)

    @admin.display(description="Owner")
    def owner(self, obj):
        return obj.column.user
