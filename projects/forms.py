from django import forms
from django.core.exceptions import ValidationError

from .models import Project, ProjectLink


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']


class ProjectLinkForm(forms.ModelForm):
    class Meta:
        model = ProjectLink
        fields = ['project', 'name', 'url']
        widgets = {'project': forms.HiddenInput()}

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['project'].queryset = Project.objects.filter(user=user)

    def clean_project(self):
        project = self.cleaned_data['project']
        if self.user and project.user_id != self.user.id:
            raise ValidationError('Invalid project.')
        return project
