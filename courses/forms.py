from django import forms

from .models import CourseLink


class CourseLinkForm(forms.ModelForm):
    class Meta:
        model = CourseLink
        fields = ["title", "url", "link_type"]
