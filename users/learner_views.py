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
from django.http import JsonResponse

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from certificates.models import Certificate
from django.utils import timezone


from courses.forms import CourseForm, LearningResourceFormSet, ScormResourceForm
from courses.models import (Course, CourseCategory, Enrollment, LearningResource, ScormResource, Tag, Program)
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
    # context_object_name = 'courses'

    # def get_queryset(self):
    #     user = self.request.user
    #     return CourseDelivery.objects.filter(enrollment__user=user).annotate(
    #         resource_count=Count('course__resources')
    #     )

@method_decorator(login_required, name='dispatch')
class LearnerCourseDetailView(DetailView):
    # model = CourseDelivery
    template_name = 'users/learner/course_course_detail.html'
    # context_object_name = 'course'

    # def get_object(self):
    #     course_id = self.kwargs.get('course_id')
    #     return get_object_or_404(CourseDelivery, id=course_id)
    
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['SCORM_API_BASE_URL'] = settings.SCORM_API_BASE_URL
    #     context['SCORM_PLAYER_USER_ID'] = self.request.user.scorm_profile.scorm_player_id
    #     context['SCORM_PLAYER_API_TOKEN'] = self.request.user.scorm_profile.token

    #     context['resource_count'] = LearningResource.objects.filter(course=self.object.course).count()
        
    #     return context
    
@method_decorator(login_required, name='dispatch')
class LearnerCalendarView(TemplateView):
    template_name = 'users/learner/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class LearnerMessageListView(TemplateView):
    template_name = 'users/learner/messages.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class LearnerAssigmentListView(TemplateView):
    template_name = 'users/learner/assignments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class LearnerGradesView(TemplateView):
    template_name = 'users/learner/grades.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class LearnerResourceView(TemplateView):
    template_name = 'users/learner/resource.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class LearnerProgressView(TemplateView):
    template_name = 'users/learner/progress.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class LearnerForumView(TemplateView):
    template_name = 'users/learner/forum.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class LearnerCertificateView(LoginRequiredMixin, TemplateView):
    template_name = 'users/learner/certificate.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get certificates for the logged-in learner
        certificates = Certificate.objects.filter(learner=self.request.user.learner).order_by('-issue_date')
        
        # Get certificate counts
        context['certificates'] = certificates
        context['total_certificates'] = certificates.count()
        context['this_year_certificates'] = certificates.filter(issue_date__year=timezone.now().year).count()
        
        # Get certificate counts by category
        certificate_types = certificates.values('course__category__name').annotate(count=Count('id'))
        
        # Initialize counts for each certificate type
        context['course_certificates'] = 0
        context['specialization_certificates'] = 0
        context['professional_certificates'] = 0

        # Categorize certificates
        for cert_type in certificate_types:
            category_name = cert_type['course__category__name']
            count = cert_type['count']
            
            if category_name == 'Course':
                context['course_certificates'] = count
            elif category_name == 'Specialization':
                context['specialization_certificates'] = count
            elif category_name == 'Professional':
                context['professional_certificates'] = count

        return context
    
@method_decorator(login_required, name='dispatch')
class LearnerBadgeView(TemplateView):
    template_name = 'users/learner/badge.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class LearnerLeaderboardView(TemplateView):
    template_name = 'users/learner/leaderboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class LearnerProfileView(TemplateView):
    template_name = 'users/learner/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class LearnerSettingsView(TemplateView):
    template_name = 'users/learner/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class LearnerHelpSupportView(TemplateView):
    template_name = 'users/learner/help_support.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class LearnerCourseLibraryView(ListView):
    template_name = 'users/learner/course_library.html'
    context_object_name = 'courses'

    def get_queryset(self):
        return Course.objects.all().prefetch_related('resources')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_course'] = self.get_queryset().first()  # You might want to choose a featured course differently
        return context

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            course_id = request.GET.get('course_id')
            if course_id:
                course = Course.objects.prefetch_related('resources').get(id=course_id)
                data = {
                    'title': course.title,
                    'description': course.description,
                    'category': course.category.name if course.category else '',
                    'resource_count': course.resources.count(),
                    'resources': [{'title': r.title} for r in course.resources.all()[:5]],
                    'cover_image': course.cover_image.url if course.cover_image else '',
                }
                return JsonResponse(data)
        return super().get(request, *args, **kwargs)
    

from django.views.generic import ListView
from django.db.models import Prefetch
from courses.models import Program, Course
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string

class LearnerProgramCatalogView(ListView):
    model = Program
    template_name = 'users/learner/program_catalog.html'
    context_object_name = 'programs'

    def get_queryset(self):
        return Program.objects.filter(is_published=True).prefetch_related(
            Prefetch('courses', queryset=Course.objects.filter(is_published=True))
        ).order_by('title')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            user_enrollments = Enrollment.objects.filter(user=self.request.user)
            enrolled_program_ids = user_enrollments.values_list('program_id', flat=True)
            for program in context['programs']:
                program.is_enrolled = program.id in enrolled_program_ids
        return context

    def post(self, request, *args, **kwargs):
        program_id = request.POST.get('program_id')
        program = get_object_or_404(Program, id=program_id)
        
        # Here you would typically handle the enrollment logic
        # For now, we'll just return a success message
        return JsonResponse({'status': 'success', 'message': 'Enrollment functionality will be implemented here.'})

    def get_administrator_course_details(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        html = render_to_string('users/learner/course_details_modal.html', {'course': course})
        return JsonResponse({'html': html})
    
def administrator_course_details(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    resources = course.resources.all()  # Changed from learning_resources to resources
    
    data = {
        'title': course.title,
        'description': course.description,
        'duration': course.duration,
        'resources': [
            {
                'title': r.title, 
                'type': r.get_resource_type_display(),
                'description': r.description
            } for r in resources
        ]
    }
    
    return JsonResponse(data)


# ============================================================
# ======================= Notifications Views ================
# ============================================================

class LearnerNotificationListView(TemplateView):
    template_name = 'users/learner/notifications/notifications_course_list.html'