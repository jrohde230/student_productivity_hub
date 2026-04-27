from django import forms


class ChecklistItemCreateForm(forms.Form):
    text = forms.CharField(max_length=255)

    def clean_text(self):
        text = self.cleaned_data["text"].strip()
        if not text:
            raise forms.ValidationError("Checklist item cannot be empty.")
        return text
