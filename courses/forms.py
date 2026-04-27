from django import forms

from .models import Course, Textbook


class CourseForm(forms.ModelForm):
    course_url = forms.URLField(required=False, label="Course URL (optional)")

    class Meta:
        model = Course
        fields = ["name", "course_url", "instructor_name", "instructor_email"]
        help_texts = {
            "name": "Shown in your course list.",
            "course_url": "Optional. When set, the course name becomes a link to this URL.",
            "instructor_name": "Optional.",
            "instructor_email": "Optional. Shown as a mailto link when provided.",
        }


class TextbookForm(forms.ModelForm):
    class Meta:
        model = Textbook
        fields = ["course", "title", "url"]
        widgets = {"course": forms.HiddenInput()}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user is not None:
            self.fields["course"].queryset = Course.objects.filter(user=user)

    def clean_course(self):
        course = self.cleaned_data["course"]
        if self.user and course.user_id != self.user.id:
            raise forms.ValidationError("Invalid course.")
        return course


class EditTextbookForm(forms.ModelForm):
    """Edit title and URL only; course cannot be changed here."""

    class Meta:
        model = Textbook
        fields = ["title", "url"]
