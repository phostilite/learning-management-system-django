from django import forms
from .models import Announcement
from django.contrib.auth import get_user_model

User = get_user_model()

# ============================================================
# ================ = Announcement Form =======================
# ============================================================
class AnnouncementForm(forms.ModelForm):
    publish_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M')
    )
    expiry_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        required=False
    )

    class Meta:
        model = Announcement
        fields = ['title', 'content', 'priority', 'publish_date', 'expiry_date']
        labels = {
            'title': 'Announcement Title',
            'content': 'Announcement Content',
            'priority': 'Priority Level',
            'publish_date': 'Publish Date',
            'expiry_date': 'Expiry Date',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.publish_date:
            self.fields['publish_date'].initial = self.instance.publish_date.strftime('%Y-%m-%dT%H:%M')
        if self.instance.expiry_date:
            self.fields['expiry_date'].initial = self.instance.expiry_date.strftime('%Y-%m-%dT%H:%M')