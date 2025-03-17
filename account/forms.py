from django import forms

from .models import Owner


class OwnerAdminForm(forms.ModelForm):
    image_upload = forms.FileField(required=False, label="Image (Upload)")

    class Meta:
        model = Owner
        fields = ["name", "url", "image_upload"]

    def save(self, commit=True):
        owner = super().save(commit=False)

        if self.cleaned_data.get("image_upload"):
            owner.image = self.cleaned_data["image_upload"].read()

        if commit:
            owner.save()

        return owner
