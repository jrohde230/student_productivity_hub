import calendar
from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from assignments.models import Assignment
from user_calendar.forms import CalendarEventForm
from user_calendar.models import CalendarEvent


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"
    success_url = reverse_lazy("dashboard")

    def _get_month_from_request(self):
        today = date.today()
        try:
            year = int(self.request.GET.get("year", today.year))
            month = int(self.request.GET.get("month", today.month))
            if month < 1 or month > 12:
                raise ValueError
        except ValueError:
            year, month = today.year, today.month
        return year, month

    def _previous_month(self, year, month):
        if month == 1:
            return year - 1, 12
        return year, month - 1

    def _next_month(self, year, month):
        if month == 12:
            return year + 1, 1
        return year, month + 1

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, month = self._get_month_from_request()
        month_start = date(year, month, 1)
        _, days_in_month = calendar.monthrange(year, month)
        month_end = date(year, month, days_in_month)

        assignments = Assignment.objects.filter(
            user=self.request.user,
            due_date__gte=month_start,
            due_date__lte=month_end,
        ).order_by("due_date", "assignment_name")
        calendar_events = CalendarEvent.objects.filter(
            user=self.request.user,
            event_date__gte=month_start,
            event_date__lte=month_end,
        ).order_by("event_date", "title")

        items_by_day = {}
        for assignment in assignments:
            day_items = items_by_day.setdefault(assignment.due_date.day, [])
            day_items.append(
                {
                    "kind": "assignment",
                    "title": assignment.assignment_name,
                    "url": assignment.assignment_url,
                }
            )

        for event in calendar_events:
            day_items = items_by_day.setdefault(event.event_date.day, [])
            day_items.append(
                {
                    "kind": "event",
                    "title": event.title,
                    "url": event.link,
                }
            )

        month_calendar = calendar.Calendar(firstweekday=6).monthdayscalendar(year, month)
        weeks = []
        for week in month_calendar:
            week_days = []
            for day in week:
                week_days.append(
                    {
                        "day": day,
                        "items": items_by_day.get(day, []) if day else [],
                    }
                )
            weeks.append(week_days)

        prev_year, prev_month = self._previous_month(year, month)
        next_year, next_month = self._next_month(year, month)

        context["calendar_year"] = year
        context["calendar_month"] = month
        context["calendar_month_label"] = month_start.strftime("%B %Y")
        context["calendar_weeks"] = weeks
        context["weekday_labels"] = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        context["prev_month_url"] = f"{self.success_url}?year={prev_year}&month={prev_month}"
        context["next_month_url"] = f"{self.success_url}?year={next_year}&month={next_month}"
        context["event_form"] = kwargs.get("event_form", CalendarEventForm(prefix="event"))
        context["open_event_modal"] = kwargs.get("open_event_modal", False)
        return context

    def post(self, request, *args, **kwargs):
        form_type = request.POST.get("form_type")
        if form_type != "add_event":
            return redirect(self.success_url)

        form = CalendarEventForm(request.POST, prefix="event")
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user
            event.save()
            messages.success(request, "Calendar event added.")
            year = event.event_date.year
            month = event.event_date.month
            return redirect(f"{self.success_url}?year={year}&month={month}")

        return self.render_to_response(
            self.get_context_data(event_form=form, open_event_modal=True)
        )
