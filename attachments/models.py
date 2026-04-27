from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models

from assignments.models import Assignment
from courses.models import Course, Textbook
from projects.models import Project
from resources.models import ResourceItem


class Attachment(models.Model):
    ALLOWED_MODELS = (Course, Textbook, Assignment, Project, ResourceItem)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    file = models.FileField(upload_to="attachments/%Y/%m/%d/")
    original_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "content_type", "object_id"]),
        ]

    def clean(self):
        model_class = self.content_type.model_class() if self.content_type_id else None
        if model_class not in self.ALLOWED_MODELS:
            raise ValidationError("This object type cannot have attachments.")

    def save(self, *args, **kwargs):
        if self.file and not self.original_name:
            self.original_name = self.file.name.split("/")[-1]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.original_name or self.file.name
