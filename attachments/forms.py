from django import forms


class AttachmentUploadForm(forms.Form):
    file = forms.FileField()
