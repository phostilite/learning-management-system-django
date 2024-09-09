import logging
import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from formtools.wizard.views import SessionWizardView
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, DetailView, ListView
from django.http import Http404

from courses.forms import CourseForm, LearningResourceFormSet, ScormResourceForm
from courses.models import (Course, CourseCategory, Enrollment, LearningResource, ScormResource, Tag, Program)
from .api_client import upload_scorm_package, register_user_for_course

logger = logging.getLogger(__name__)

User = get_user_model()

@method_decorator(login_required, name='dispatch')
class FacilitatorDashboardView(TemplateView):
    template_name = 'users/facilitator/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class FacilitatorNotificationListView(TemplateView):
    template_name = 'users/facilitator/notifications/notifications_course_list.html'
