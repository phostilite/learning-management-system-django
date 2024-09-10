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

from django_filters.views import FilterView
from .filters import ProgramFilter, CourseFilter
from django.db.models import Prefetch
from django.db.models import Avg, Q


from courses.forms import CourseForm, LearningResourceFormSet, ScormResourceForm
from courses.models import (Course, CourseCategory, Enrollment, LearningResource, ScormResource, Tag, Program, ProgramCourse, Review)
from .api_client import upload_scorm_package, register_user_for_course

logger = logging.getLogger(__name__)

User = get_user_model()

@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'users/learner/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
# ================================================================
#                           Programs Views
# ================================================================

class ProgramListView(LoginRequiredMixin, FilterView):
    model = Program
    template_name = 'users/learner/programs/program_list.html'
    context_object_name = 'programs'
    filterset_class = ProgramFilter
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['total_programs'] = self.get_queryset().count()
        except Exception as e:
            logger.error(f"Error getting total programs count: {str(e)}")
            context['total_programs'] = 0
        return context
    
class ProgramDetailView(LoginRequiredMixin, DetailView):
    model = Program
    template_name = 'users/learner/programs/program_detail.html'
    context_object_name = 'program'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # Prefetch related courses and their learning resources
            program_courses = ProgramCourse.objects.filter(program=self.object).select_related('course').prefetch_related(
                Prefetch('course__resources', queryset=LearningResource.objects.order_by('order'))
            ).order_by('order')
            
            context['program_courses'] = program_courses
            
            # Check if the user is enrolled
            context['is_enrolled'] = Enrollment.objects.filter(user=self.request.user, program=self.object).exists()
            
            # Get related programs based on shared tags
            program_tags = self.object.tags.values_list('id', flat=True)
            related_programs = Program.objects.filter(tags__in=program_tags).exclude(id=self.object.id).distinct().order_by('-created_at')[:3]
            context['related_programs'] = related_programs
            
            # Get program reviews
            reviews = Review.objects.filter(content_type__model='program', object_id=self.object.id).select_related('user').order_by('-created_at')
            context['reviews'] = reviews[:5]
            
            # Calculate average rating
            context['average_rating'] = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

            # Check if the current user has already reviewed this program
            context['user_has_reviewed'] = reviews.filter(user=self.request.user).exists()

        except Exception as e:
            logger.error(f"Error in ProgramDetailView: {str(e)}")
            context['error'] = str(e)
        
        return context
    
# ================================================================
#                           Courses Views
# ================================================================

class CourseListView(LoginRequiredMixin, FilterView):
    model = Course
    template_name = 'users/learner/courses/course_list.html'
    context_object_name = 'courses'
    filterset_class = CourseFilter
    paginate_by = 12  # Increased from 10 to 12 for better grid layout

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(is_published=True).select_related('category').prefetch_related('tags')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['total_courses'] = self.get_queryset().count()
            context['categories'] = CourseCategory.objects.all()
            
            # Get unique difficulty levels from the database
            context['difficulty_levels'] = Course.objects.values_list('difficulty_level', flat=True).distinct()
            
        except Exception as e:
            logger.error(f"Error in CourseListView get_context_data: {str(e)}")
            context['total_courses'] = 0
            context['categories'] = []
            context['difficulty_levels'] = []
        
        return context

class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'users/learner/courses/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['learning_resources'] = self.object.resources.all().order_by('order')
            
            # Get course reviews
            reviews = Review.objects.filter(content_type__model='course', object_id=self.object.id)
            context['reviews'] = reviews
            context['average_rating'] = reviews.aggregate(Avg('rating'))['rating__avg']

            # Get related courses (courses with same category or shared tags)
            related_courses = Course.objects.filter(
                Q(category=self.object.category) | Q(tags__in=self.object.tags.all())
            ).exclude(id=self.object.id).distinct()[:3]
            context['related_courses'] = related_courses

        except Exception as e:
            logger.error(f"Error in CourseDetailView get_context_data: {str(e)}")
            context['learning_resources'] = []
            context['reviews'] = []
            context['average_rating'] = None
            context['related_courses'] = []

        return context
    

@method_decorator(login_required, name='dispatch')
class CalendarView(TemplateView):
    template_name = 'users/learner/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class MessageListView(TemplateView):
    template_name = 'users/learner/messages.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class AssigmentListView(TemplateView):
    template_name = 'users/learner/assignments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class GradesView(TemplateView):
    template_name = 'users/learner/grades.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class ResourceView(TemplateView):
    template_name = 'users/learner/resource.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class ProgressView(TemplateView):
    template_name = 'users/learner/progress.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class ForumView(TemplateView):
    template_name = 'users/learner/forum.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class CertificateView(LoginRequiredMixin, TemplateView):
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
class BadgeView(TemplateView):
    template_name = 'users/learner/badge.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class LeaderboardView(TemplateView):
    template_name = 'users/learner/leaderboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
    template_name = 'users/learner/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class SettingsView(TemplateView):
    template_name = 'users/learner/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class HelpSupportView(TemplateView):
    template_name = 'users/learner/help_support.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
    
# ============================================================
# ======================= Notifications Views ================
# ============================================================

class NotificationListView(TemplateView):
    template_name = 'users/learner/notifications/notifications_course_list.html'