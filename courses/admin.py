from django.contrib import admin

from .models import Course, Textbook


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "instructor_name", "instructor_email", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "instructor_name", "instructor_email", "user__username", "user__email")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)
    fieldsets = (
        (None, {"fields": ("user", "name", "course_url")}),
        ("Instructor (optional)", {"fields": ("instructor_name", "instructor_email")}),
        ("Meta", {"fields": ("created_at",)}),
    )


@admin.register(Textbook)
class TextbookAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "user", "url", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "url", "course__name", "user__username", "user__email")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("course",)

    @admin.display(description="User")
    def user(self, obj):
        return obj.course.user
