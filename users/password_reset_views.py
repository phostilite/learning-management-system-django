import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import FormView, TemplateView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django import forms
from django.urls import reverse_lazy

logger = logging.getLogger(__name__)

User = get_user_model()

class PasswordResetForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254)

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            raise ValidationError("There is no user registered with this email address.")
        return email

class SetPasswordForm(forms.Form):
    new_password1 = forms.CharField(label="New password", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Confirm new password", widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password fields didn't match.")
        return cleaned_data
    
class PasswordResetView(FormView):
    template_name = 'users/password_reset/password_reset_form.html'
    form_class = PasswordResetForm
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        user = User.objects.filter(email=email).first()
        if user:
            # Generate token and uid
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build reset URL
            reset_url = self.request.build_absolute_uri(
                reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            
            # Render email template
            context = {
                'user': user,
                'reset_url': reset_url,
                'uid': uid,
                'token': token,
                'protocol': 'https' if self.request.is_secure() else 'http',
                'domain': self.request.get_host(),
            }
            email_body = render_to_string('users/password_reset/password_reset_email.html', context)
            
            # Send email
            send_mail(
                'Password Reset Request',
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        
        return super().form_valid(form)

class PasswordResetDoneView(TemplateView):
    template_name = 'users/password_reset/password_reset_done.html'

class PasswordResetConfirmView(FormView):
    template_name = 'users/password_reset/password_reset_confirm.html'
    form_class = SetPasswordForm
    success_url = reverse_lazy('password_reset_complete')

    def dispatch(self, *args, **kwargs):
        try:
            uid = urlsafe_base64_decode(kwargs['uidb64']).decode()
            self.user = User.objects.get(pk=uid)
            if not default_token_generator.check_token(self.user, kwargs['token']):
                logger.warning(f"Invalid password reset attempt for user {uid}")
                messages.error(self.request, "The password reset link is invalid or has expired.")
                return redirect('password_reset')
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            logger.error(f"Error in password reset confirmation: {str(e)}")
            messages.error(self.request, "The password reset link is invalid or has expired.")
            return redirect('password_reset')
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        try:
            new_password = form.cleaned_data['new_password1']
            self.user.set_password(new_password)
            self.user.save()
            logger.info(f"Password reset successful for user {self.user.email}")
            messages.success(self.request, "Your password has been reset successfully.")
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error setting new password for user {self.user.email}: {str(e)}")
            messages.error(self.request, "An error occurred. Please try again.")
            return self.form_invalid(form)

class PasswordResetCompleteView(TemplateView):
    template_name = 'users/password_reset/password_reset_complete.html'