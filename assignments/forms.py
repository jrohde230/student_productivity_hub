from django import forms

from .models import Assignment


class AssignmentForm(forms.ModelForm):
    due_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    assignment_url = forms.URLField(required=False)

    class Meta:
        model = Assignment
        fields = ["class_name", "assignment_name", "assignment_url", "due_date", "subject"]


class EditAssignmentForm(forms.ModelForm):
    assignment_id = forms.IntegerField(widget=forms.HiddenInput)
    due_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    assignment_url = forms.URLField(required=False)

    class Meta:
        model = Assignment
        fields = ["assignment_id", "class_name", "assignment_name", "assignment_url", "due_date", "subject"]

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_assignment_id(self):
        assignment_id = self.cleaned_data["assignment_id"]
        assignment = Assignment.objects.filter(pk=assignment_id, user=self.user).first()
        if not assignment:
            raise forms.ValidationError("Assignment not found.")
        return assignment_id

    def save(self, commit=True):
        assignment = Assignment.objects.get(pk=self.cleaned_data["assignment_id"], user=self.user)
        for field in ["class_name", "assignment_name", "assignment_url", "due_date", "subject"]:
            setattr(assignment, field, self.cleaned_data[field])
        if commit:
            assignment.save()
        return assignment
