from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings

from assignments.models import Assignment
from courses.models import Course, Textbook
from projects.models import Project
from resources.models import ResourceItem


class Note(models.Model):
    ALLOWED_MODELS = (Course, Textbook, Assignment, Project, ResourceItem)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "content_type", "object_id"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def clean(self):
        model_class = self.content_type.model_class() if self.content_type_id else None
        if model_class not in self.ALLOWED_MODELS:
            raise ValidationError("This object type cannot have notes.")

    def __str__(self):
        return f"Note #{self.pk}"
