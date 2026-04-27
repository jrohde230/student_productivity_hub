from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import Project, ProjectComment, ProjectLink

User = get_user_model()


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
            self.fields['project'].queryset = Project.objects.filter(
                Q(user=user) | Q(collaborators__user=user)
            ).distinct()

    def clean_project(self):
        project = self.cleaned_data['project']
        is_owner = project.user_id == self.user.id
        is_collaborator = project.collaborators.filter(user=self.user).exists()
        if self.user and not (is_owner or is_collaborator):
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
        project = Project.objects.filter(
            Q(pk=project_id),
            Q(user=self.user) | Q(collaborators__user=self.user),
        ).distinct().first()
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
        link = ProjectLink.objects.filter(
            Q(pk=link_id),
            Q(project__user=self.user) | Q(project__collaborators__user=self.user),
        ).distinct().first()
        if not link:
            raise ValidationError('Invalid project link.')
        self._link = link
        return cleaned

    def save(self):
        self._link.name = self.cleaned_data['name']
        self._link.url = self.cleaned_data['url']
        self._link.save(update_fields=['name', 'url'])
        return self._link


class CollaboratorInviteForm(forms.Form):
    email = forms.EmailField()

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class ProjectCommentForm(forms.ModelForm):
    class Meta:
        model = ProjectComment
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 2})}
