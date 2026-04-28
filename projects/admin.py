from django.contrib import admin

from .models import Project, ProjectCollaborator, ProjectComment, ProjectLink


class ProjectLinkInline(admin.TabularInline):
    model = ProjectLink
    extra = 0


class ProjectCollaboratorInline(admin.TabularInline):
    model = ProjectCollaborator
    autocomplete_fields = ("user", "added_by")
    extra = 0


class ProjectCommentInline(admin.TabularInline):
    model = ProjectComment
    autocomplete_fields = ("user",)
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "description", "user__username", "user__email")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)
    inlines = (ProjectLinkInline, ProjectCollaboratorInline, ProjectCommentInline)


@admin.register(ProjectLink)
class ProjectLinkAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "owner", "url", "created_at")
    search_fields = ("name", "url", "project__name", "project__user__username")
    autocomplete_fields = ("project",)
    readonly_fields = ("created_at",)

    @admin.display(description="Owner")
    def owner(self, obj):
        return obj.project.user


@admin.register(ProjectCollaborator)
class ProjectCollaboratorAdmin(admin.ModelAdmin):
    list_display = ("project", "user", "added_by", "created_at")
    search_fields = (
        "project__name",
        "user__username",
        "user__email",
        "added_by__username",
    )
    autocomplete_fields = ("project", "user", "added_by")
    readonly_fields = ("created_at",)


@admin.register(ProjectComment)
class ProjectCommentAdmin(admin.ModelAdmin):
    list_display = ("short_body", "project", "user", "created_at")
    search_fields = ("body", "project__name", "user__username")
    autocomplete_fields = ("project", "user")
    readonly_fields = ("created_at",)

    @admin.display(description="Comment")
    def short_body(self, obj):
        text = obj.body.strip()
        return text[:80] + ("…" if len(text) > 80 else "")
