from django import forms

from .models import CalendarEvent


class CalendarEventForm(forms.ModelForm):
    event_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    link = forms.URLField(required=False)

    class Meta:
        model = CalendarEvent
        fields = ["title", "event_date", "link"]
