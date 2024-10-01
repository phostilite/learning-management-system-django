from django import forms
from .models import Announcement
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field
from .models import AnnouncementRecipient
from django.contrib.contenttypes.models import ContentType
from users.models import User
from courses.models import Course, Program

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


class AnnouncementRecipientForm(forms.ModelForm):
    specific_recipient = forms.CharField(
        required=False,
        help_text="Enter username, course code, or program code based on recipient type"
    )

    class Meta:
        model = AnnouncementRecipient
        fields = ['recipient_type', 'specific_recipient']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('recipient_type', css_class='mb-3'),
            Field('specific_recipient', css_class='mb-3'),
            Submit('submit', 'Add Recipient', css_class='inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-md transition duration-300 ease-in-out transform hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50')
        )

    def clean(self):
        cleaned_data = super().clean()
        recipient_type = cleaned_data.get('recipient_type')
        specific_recipient = cleaned_data.get('specific_recipient')

        if recipient_type in ['USER', 'COURSE', 'PROGRAM'] and not specific_recipient:
            raise forms.ValidationError("Specific recipient is required for this recipient type.")

        if recipient_type == 'USER':
            try:
                user = User.objects.get(username=specific_recipient)
                cleaned_data['content_type'] = ContentType.objects.get_for_model(User)
                cleaned_data['object_id'] = user.id
            except User.DoesNotExist:
                raise forms.ValidationError("User does not exist.")
        elif recipient_type == 'COURSE':
            try:
                course = Course.objects.get(code=specific_recipient)
                cleaned_data['content_type'] = ContentType.objects.get_for_model(Course)
                cleaned_data['object_id'] = course.id
            except Course.DoesNotExist:
                raise forms.ValidationError("Course does not exist.")
        elif recipient_type == 'PROGRAM':
            try:
                program = Program.objects.get(code=specific_recipient)
                cleaned_data['content_type'] = ContentType.objects.get_for_model(Program)
                cleaned_data['object_id'] = program.id
            except Program.DoesNotExist:
                raise forms.ValidationError("Program does not exist.")

        return cleaned_data