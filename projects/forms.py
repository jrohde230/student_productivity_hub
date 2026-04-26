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


class EditProjectForm(forms.Form):
    project_id = forms.IntegerField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=200)
    description = forms.CharField(required=False, widget=forms.Textarea)

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        self._project = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        project_id = cleaned.get('project_id')
        if project_id is None or self.user is None:
            return cleaned
        project = Project.objects.filter(pk=project_id, user=self.user).first()
        if not project:
            raise ValidationError('Invalid project.')
        self._project = project
        return cleaned

    def save(self):
        self._project.name = self.cleaned_data['name']
        self._project.description = self.cleaned_data['description']
        self._project.save(update_fields=['name', 'description'])
        return self._project


class EditProjectLinkForm(forms.Form):
    link_id = forms.IntegerField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=200)
    url = forms.URLField(max_length=500)

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        self._link = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        link_id = cleaned.get('link_id')
        if link_id is None or self.user is None:
            return cleaned
        link = ProjectLink.objects.filter(pk=link_id, project__user=self.user).first()
        if not link:
            raise ValidationError('Invalid project link.')
        self._link = link
        return cleaned

    def save(self):
        self._link.name = self.cleaned_data['name']
        self._link.url = self.cleaned_data['url']
        self._link.save(update_fields=['name', 'url'])
        return self._link
