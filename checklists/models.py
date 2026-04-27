from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models

from assignments.models import Assignment
from projects.models import Project


class ChecklistItem(models.Model):
    ALLOWED_MODELS = (Assignment, Project)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="checklist_items",
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    text = models.CharField(max_length=255)
    is_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["is_done", "created_at", "text"]
        indexes = [
            models.Index(fields=["user", "content_type", "object_id"]),
        ]

    def clean(self):
        model_class = self.content_type.model_class() if self.content_type_id else None
        if model_class not in self.ALLOWED_MODELS:
            raise ValidationError("This object type cannot have checklist items.")

    def __str__(self):
        return self.text
