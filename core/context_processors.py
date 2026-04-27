from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from assignments.models import Assignment


def upcoming_due_notifications(request):
    if not request.user.is_authenticated:
        return {
            "upcoming_notifications": [],
            "upcoming_notifications_count": 0,
        }

    today = timezone.localdate()
    horizon = today + timedelta(days=7)
    assignments = (
        Assignment.objects.filter(
            user=request.user,
            due_date__gte=today,
            due_date__lte=horizon,
        )
        .order_by("due_date", "assignment_name")[:8]
    )

    notifications = []
    for assignment in assignments:
        days_left = (assignment.due_date - today).days
        if days_left == 0:
            timing = "Due today"
        elif days_left == 1:
            timing = "Due tomorrow"
        else:
            timing = f"Due in {days_left} days"

        notifications.append(
            {
                "title": assignment.assignment_name,
                "class_name": assignment.class_name,
                "due_date": assignment.due_date,
                "timing": timing,
                "url": assignment.assignment_url or reverse("assignments:home"),
            }
        )

    return {
        "upcoming_notifications": notifications,
        "upcoming_notifications_count": len(notifications),
    }
