from django import forms
from django.forms import inlineformset_factory
from .models import Quiz, Question, Choice

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'time_limit', 'passing_score', 'max_attempts', 'is_active']

class QuestionForm(forms.ModelForm):
    short_answer_key = forms.CharField(required=False)
    essay_rubric = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        model = Question
        fields = ['text', 'question_type', 'points', 'order']

QuestionFormSet = inlineformset_factory(
    Quiz, Question, form=QuestionForm, extra=1, can_delete=True
)

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['text', 'is_correct']

ChoiceFormSet = inlineformset_factory(
    Question, Choice, form=ChoiceForm, extra=3, can_delete=True
)