from django import forms

from .models import Assignment


class AssignmentForm(forms.ModelForm):
    due_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    assignment_url = forms.URLField(required=False)

    class Meta:
        model = Assignment
        fields = ["class_name", "assignment_name", "assignment_url", "due_date", "subject"]
