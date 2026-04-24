from django.conf import settings
from django.db import models


class ResourceColumn(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resource_columns",
    )
    slot = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=100)

    class Meta:
        ordering = ["slot"]
        constraints = [
            models.UniqueConstraint(fields=["user", "slot"], name="unique_resource_column_slot_per_user"),
        ]

    def __str__(self):
        return self.title


class ResourceItem(models.Model):
    column = models.ForeignKey(
        ResourceColumn,
        on_delete=models.CASCADE,
        related_name="items",
    )
    name = models.CharField(max_length=200)
    url = models.URLField(max_length=500)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "created_at", "name"]

    def __str__(self):
        return self.name
