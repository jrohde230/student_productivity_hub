from django.db import models
from django.conf import settings


class CourseLink(models.Model):
    TEXTBOOK = "textbook"
    LEARNING_ENVIRONMENT = "learning_environment"
    LINK_TYPE_CHOICES = [
        (TEXTBOOK, "Textbook"),
        (LEARNING_ENVIRONMENT, "Learning Environment"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="course_links")
    title = models.CharField(max_length=200)
    url = models.URLField(max_length=500)
    link_type = models.CharField(max_length=30, choices=LINK_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_link_type_display()})"
