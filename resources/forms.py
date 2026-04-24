from django import forms
from django.core.exceptions import ValidationError

from .models import ResourceColumn, ResourceItem


class RenameColumnForm(forms.Form):
    column = forms.ModelChoiceField(
        queryset=ResourceColumn.objects.none(),
        widget=forms.HiddenInput(),
    )
    title = forms.CharField(max_length=100, label="Column name")

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["column"].queryset = ResourceColumn.objects.filter(user=user)

    def clean_column(self):
        column = self.cleaned_data["column"]
        if self.user and column.user_id != self.user.id:
            raise ValidationError("Invalid column.")
        return column


class AddResourceForm(forms.ModelForm):
    class Meta:
        model = ResourceItem
        fields = ["column", "name", "url"]
        widgets = {"column": forms.HiddenInput()}

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["column"].queryset = ResourceColumn.objects.filter(user=user)

    def clean_column(self):
        column = self.cleaned_data["column"]
        if self.user and column.user_id != self.user.id:
            raise ValidationError("Invalid column.")
        return column


class EditResourceForm(forms.Form):
    resource_id = forms.IntegerField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=200)
    url = forms.URLField(max_length=500)

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        self._item = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        rid = cleaned.get("resource_id")
        if rid is None or self.user is None:
            return cleaned
        item = ResourceItem.objects.filter(pk=rid, column__user=self.user).first()
        if not item:
            raise ValidationError("Invalid resource.")
        self._item = item
        return cleaned

    def save(self):
        self._item.name = self.cleaned_data["name"]
        self._item.url = self.cleaned_data["url"]
        self._item.save(update_fields=["name", "url"])
        return self._item
