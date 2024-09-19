from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm as BasePasswordChangeForm
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class LoginForm(AuthenticationForm):
    """Form for logging in users."""
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Username'}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Password'}
        )
    )

    class Meta:
        """Meta class for LoginForm."""
        fields = ['username', 'password']

class LearnerCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data


class PersonalInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'gender']

class PasswordChangeForm(BasePasswordChangeForm):
    pass

class PreferencesForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['preferred_language', 'timezone', 'email_notifications_enabled', 'sms_notifications_enabled']

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['picture']
        widgets = {
            'picture': forms.FileInput(attrs={'accept': 'image/*'})
        }

    def clean_picture(self):
        picture = self.cleaned_data.get('picture')
        if picture:
            if picture.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError(_("Image file too large ( > 5MB )"))
            if picture.content_type not in ['image/jpeg', 'image/png', 'image/gif']:
                raise forms.ValidationError(_("Unsupported file type. Please upload a JPEG, PNG, or GIF image."))
        return picture