# forms.py
from django import forms
from .models import Message, Thread
from django.contrib.auth import get_user_model

User = get_user_model()

class MessageForm(forms.Form):
    recipient_email = forms.EmailField(
        label='Recipient Email',
        required=False
    )
    subject = forms.CharField(
        max_length=255,
        required=True
    )
    content = forms.CharField(
        widget=forms.Textarea,
        required=True
    )

    def clean_recipient_email(self):
        email = self.cleaned_data['recipient_email']
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("No user found with this email address")
        return email