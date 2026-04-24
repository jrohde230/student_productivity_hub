from django.db import models
from django.conf import settings


class Assignment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assignments")
    class_name = models.CharField(max_length=120)
    assignment_name = models.CharField(max_length=200)
    assignment_url = models.URLField(max_length=500, blank=True)
    due_date = models.DateField()
    subject = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date", "assignment_name"]

    def __str__(self):
        return f"{self.assignment_name} - {self.class_name}"
