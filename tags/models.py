from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models

from assignments.models import Assignment
from courses.models import Course, Textbook
from projects.models import Project
from resources.models import ResourceItem


class Tag(models.Model):
    ALLOWED_MODELS = (Course, Textbook, Assignment, Project, ResourceItem)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tags",
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    label = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["label", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "content_type", "object_id", "label"],
                name="unique_tag_per_item_for_user",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "label"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def clean(self):
        model_class = self.content_type.model_class() if self.content_type_id else None
        if model_class not in self.ALLOWED_MODELS:
            raise ValidationError("This object type cannot have tags.")

    def save(self, *args, **kwargs):
        label = self.label.strip().lower()
        if label and not label.startswith("#"):
            label = f"#{label}"
        self.label = label
        super().save(*args, **kwargs)

    def __str__(self):
        return self.label
