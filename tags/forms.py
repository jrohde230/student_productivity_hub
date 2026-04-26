from django import forms


class TagCreateForm(forms.Form):
    label = forms.CharField(max_length=64)

    def clean_label(self):
        label = self.cleaned_data["label"].strip().lower()
        if not label:
            raise forms.ValidationError("Tag cannot be empty.")
        if not label.startswith("#"):
            label = f"#{label}"
        return label
