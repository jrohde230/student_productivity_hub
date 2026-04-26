from django import forms


class NoteCreateForm(forms.Form):
    body = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), max_length=2000)


class NoteEditForm(forms.Form):
    note_id = forms.IntegerField(widget=forms.HiddenInput())
    body = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), max_length=2000)
