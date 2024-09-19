# forms.py

from django import forms
from .models import SupportTicket, SupportCategory

class TicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['title', 'description', 'category', 'priority', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a brief title for your ticket'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide a detailed description of your issue'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
           'priority': forms.Select(attrs={
                'class': 'form-control',
                'required': False
            }),
            'status': forms.Select(attrs={
                'class': 'form-control',
                'required': False
            })
        }
        help_texts = {
            'title': 'A short, descriptive title for your support ticket.',
            'description': 'Please provide as much detail as possible about your issue.',
            'category': 'Select the category that best fits your issue.',
            'priority': 'Choose the priority level for your ticket.'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = SupportCategory.objects.all()
        self.fields['priority'].required = False
        self.fields['status'].required = False
        

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise forms.ValidationError("The title must be at least 5 characters long.")
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description) < 20:
            raise forms.ValidationError("Please provide a more detailed description (at least 20 characters).")
        return description
