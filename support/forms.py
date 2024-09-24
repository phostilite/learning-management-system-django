# forms.py

from django import forms
from .models import SupportTicket, SupportCategory,FAQ

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


class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ['question', 'answer']
        widgets = {
            'question': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter the frequently asked question'
            }),
            'answer': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide a detailed answer to the question'
            }),
            

        }
        help_texts = {
            'question': 'The frequently asked question.',
            'answer': 'A comprehensive answer to the question.',
            'category': 'Select the category this FAQ belongs to.',
            'is_published': 'Check this if the FAQ should be visible to users.'
        }


    def clean_question(self):
        question = self.cleaned_data.get('question')
        if len(question) < 10:
            raise forms.ValidationError("The question must be at least 10 characters long.")
        return question

    def clean_answer(self):
        answer = self.cleaned_data.get('answer')
        if len(answer) < 30:
            raise forms.ValidationError("Please provide a more detailed answer (at least 30 characters).")
        return answer