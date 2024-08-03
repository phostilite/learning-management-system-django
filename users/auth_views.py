import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views import View
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseServerError
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters

from .forms import LoginForm

logger = logging.getLogger(__name__)


class LoginView(LoginView):
    """Custom login view."""

    template_name = 'users/authentication/login.html'
    form_class = LoginForm

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        """Handle dispatch for the login view."""
        if self.request.user.is_authenticated:
            return self.redirect_authenticated_user(self.request.user)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Handle valid form submission."""
        login(self.request, form.get_user())
        logger.info("User %s logged in successfully.", form.get_user().username)
        messages.success(self.request, _('You have successfully logged in.'))
        return self.redirect_authenticated_user(form.get_user())

    def form_invalid(self, form):
        """Handle invalid form submission."""
        logger.warning("Failed login attempt for username: %s", form.data.get('username'))
        error_messages = self._get_error_messages(form)
        messages.error(self.request, _('Login failed. Please check the errors below.'))
        return self.render_to_response(self.get_context_data(form=form, error_messages=error_messages))

    def get_form_kwargs(self):
        """Get keyword arguments for the form."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def redirect_authenticated_user(self, user):
        """Redirect users based on their group."""
        if user.groups.filter(name='administrator').exists():
            return redirect('administrator_dashboard')
        elif user.groups.filter(name='facilitator').exists():
            return redirect('facilitator_dashboard')
        elif user.groups.filter(name='learner').exists():
            return redirect('learner_dashboard')
        elif user.groups.filter(name='supervisor').exists():
            return redirect('supervisor_dashboard')
        else:
            return HttpResponseServerError("User group not found.")

    def get_context_data(self, **kwargs):
        """Get context data for the template."""
        context = super().get_context_data(**kwargs)
        google_error_messages = self.request.session.pop('error_messages', None)
        if google_error_messages:
            context['error_messages'] = google_error_messages
        return context

    @staticmethod
    def _get_error_messages(form):
        """Get error messages from form errors."""
        error_messages = []
        for field, errors in form.errors.items():
            for error in errors:
                if field == '__all__':
                    error_messages.append(str(error))
                else:
                    error_messages.append(f"{field.capitalize()}: {error}")
        return error_messages
    
class SignupView(View):
    template_name = 'users/authentication/signup.html'

    def get(self, request):
        return render(request, self.template_name)


def user_logout(request):
    """Log out the user."""
    try:
        logout(request)
        return redirect('login')
    except Exception as e:
        logger.error("Error during user logout: %s", str(e))
        return HttpResponseServerError("An error occurred during logout.")