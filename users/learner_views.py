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
from django.shortcuts import get_object_or_404


from courses.forms import CourseBasicInfoForm, LearningResourceFormSet, ScormResourceForm
from courses.models import (Attendance, Course, CourseCategory, CourseDelivery, 
                            Enrollment, Feedback, LearningResource, ScormResource)
from .api_client import upload_scorm_package, register_user_for_course

logger = logging.getLogger(__name__)

User = get_user_model()

@method_decorator(login_required, name='dispatch')
class LearnerDashboardView(TemplateView):
    template_name = 'users/learner/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class LearnerMyCoursesView(ListView):
    template_name = 'users/learner/my_courses.html'
    context_object_name = 'courses'

    def get_queryset(self):
        user = self.request.user
        return CourseDelivery.objects.filter(enrollment__user=user)

@method_decorator(login_required, name='dispatch')
class LearnerCourseDetailView(DetailView):
    model = CourseDelivery
    template_name = 'users/learner/course_detail.html'
    context_object_name = 'course'

    def get_object(self):
        course_id = self.kwargs.get('course_id')
        return get_object_or_404(CourseDelivery, id=course_id)