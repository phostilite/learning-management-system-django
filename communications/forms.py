from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

class NewMessageForm(forms.Form):
    recipient = forms.ModelChoiceField(
        queryset=get_user_model().objects.all(),
        label=_("Recipient"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    subject = forms.CharField(
        max_length=255,
        label=_("Subject"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        label=_("Message")
    )