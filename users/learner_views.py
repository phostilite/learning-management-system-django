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
from courses.models import (Course, CourseCategory, Enrollment, LearningResource, ScormResource, Tag, Program, ProgramCourse, Review, Progress, DeliveryComponent, Delivery)
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
            program_courses = ProgramCourse.objects.filter(program=self.object).select_related('course').prefetch_related(
                Prefetch('course__resources', queryset=LearningResource.objects.order_by('order'))
            ).order_by('order')
            context['program_courses'] = program_courses
            context['is_enrolled'] = Enrollment.objects.filter(user=self.request.user, program=self.object).exists()
            program_tags = self.object.tags.values_list('id', flat=True)
            related_programs = Program.objects.filter(tags__in=program_tags).exclude(id=self.object.id).distinct().order_by('-created_at')[:3]
            context['related_programs'] = related_programs
            reviews = Review.objects.filter(content_type__model='program', object_id=self.object.id).select_related('user').order_by('-created_at')
            context['reviews'] = reviews[:5]
            context['average_rating'] = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
            context['user_has_reviewed'] = reviews.filter(user=self.request.user).exists()
        except Exception as e:
            logger.error(f"Error in ProgramDetailView: {str(e)}")
            context['error'] = str(e)
        return context
    

class MyProgramsView(LoginRequiredMixin, ListView):
    template_name = 'users/learner/programs/my_programs.html'
    context_object_name = 'enrollments'
    paginate_by = 10

    def get_queryset(self):
        try:
            enrollments = Enrollment.objects.filter(
                Q(user=self.request.user, program__isnull=False) |
                Q(user=self.request.user, delivery__delivery_type='PROGRAM')
            ).select_related('program', 'delivery', 'delivery__program').order_by('-enrollment_date')
            
            for enrollment in enrollments:
                if enrollment.program:
                    enrollment.current_program = enrollment.program
                    enrollment.enrollment_type = 'direct'
                elif enrollment.delivery and enrollment.delivery.program:
                    enrollment.current_program = enrollment.delivery.program
                    enrollment.enrollment_type = 'delivery'
                else:
                    enrollment.current_program = None
                    enrollment.enrollment_type = 'unknown'
            
            return enrollments
        except Exception as e:
            logger.error(f"Error fetching enrollments for user {self.request.user.id}: {str(e)}", exc_info=True)
            return Enrollment.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['total_enrollments'] = self.get_queryset().count()
        except Exception as e:
            logger.error(f"Error getting total enrollments count: {str(e)}", exc_info=True)
            context['total_enrollments'] = 0
        return context
    
class MyProgramDetailsView(LoginRequiredMixin, DetailView):
    template_name = 'users/learner/programs/my_program_details.html'
    context_object_name = 'program'

    def get_object(self):
        program_id = self.kwargs.get('program_id')
        return get_object_or_404(Program, id=program_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        program = self.object

        enrollment = Enrollment.objects.filter(
            user=user,
            program=program
        ).first() or Enrollment.objects.filter(
            user=user,
            delivery__program=program,
            delivery__delivery_type='PROGRAM'
        ).first()

        if not enrollment:
            context['error'] = "You are not enrolled in this program."
            return context

        context['enrollment'] = enrollment

        if enrollment.delivery:
            # Fetch top-level delivery components (courses for program delivery)
            delivery_components = DeliveryComponent.objects.filter(
                delivery=enrollment.delivery,
                parent_component__isnull=True
            ).order_by('order')

            # Fetch sub-components (learning resources) for each course component
            for component in delivery_components:
                if component.is_course_component:
                    component.sub_components = DeliveryComponent.objects.filter(
                        parent_component=component
                    ).order_by('order')

            context['delivery_components'] = delivery_components

            # Fetch progress for all components
            all_components = DeliveryComponent.objects.filter(delivery=enrollment.delivery)
            progress_records = Progress.objects.filter(
                enrollment=enrollment,
                learning_resource__in=[dc.learning_resource for dc in all_components if dc.learning_resource]
            )
            context['component_progress'] = {p.learning_resource_id: p for p in progress_records}

            # Fetch course progress
            course_progress = Progress.objects.filter(
                enrollment=enrollment,
                course__in=[dc.program_course.course for dc in delivery_components if dc.program_course]
            )
            context['course_progress'] = {p.course_id: p for p in course_progress}
        else:
            # Direct program enrollment
            program_courses = program.program_courses.all().select_related('course').order_by('order')
            context['program_courses'] = program_courses

            # Fetch progress for the program and its courses
            progress_records = Progress.objects.filter(
                enrollment=enrollment,
                program=program
            ).select_related('course')
            context['program_progress'] = progress_records.filter(course__isnull=True).first()
            context['course_progress'] = {p.course_id: p for p in progress_records.filter(course__isnull=False)}

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
    
class MyCoursesView(LoginRequiredMixin, ListView):
    template_name = 'users/learner/courses/my_courses.html'
    context_object_name = 'enrollments'

    def get_queryset(self):
        try:
            return Enrollment.objects.filter(
                Q(user=self.request.user, course__isnull=False) |
                Q(user=self.request.user, delivery__delivery_type='COURSE')
            ).select_related('course', 'delivery', 'delivery__course').order_by('-enrollment_date')
        except Exception as e:
            logger.error(f"Error fetching course enrollments for user {self.request.user.id}: {str(e)}")
            return Enrollment.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['total_enrollments'] = self.get_queryset().count()
        except Exception as e:
            logger.error(f"Error getting total course enrollments count: {str(e)}")
            context['total_enrollments'] = 0
        return context

class MyCourseDetailsView(LoginRequiredMixin, DetailView):
    template_name = 'users/learner/courses/my_course_details.html'
    context_object_name = 'course'

    def get_object(self):
        course_id = self.kwargs.get('course_id')
        try:
            return get_object_or_404(Course, id=course_id)
        except Exception as e:
            logger.error(f"Error fetching course with id {course_id}: {str(e)}")
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            course = self.object
            user = self.request.user

            # Get enrollment (direct or through delivery)
            enrollment = Enrollment.objects.filter(
                Q(user=user, course=course) |
                Q(user=user, delivery__course=course, delivery__delivery_type='COURSE')
            ).select_related('delivery').first()

            if not enrollment:
                context['error'] = "You are not enrolled in this course."
                return context

            context['enrollment'] = enrollment

            if enrollment.delivery:
                # Enrollment through delivery
                delivery_components = DeliveryComponent.objects.filter(
                    delivery=enrollment.delivery
                ).select_related('learning_resource').order_by('order')
                context['delivery_components'] = delivery_components
                
                # Fetch progress for delivery components
                progress_records = Progress.objects.filter(
                    enrollment=enrollment,
                    learning_resource__in=[dc.learning_resource for dc in delivery_components if dc.learning_resource]
                )
                context['component_progress'] = {p.learning_resource_id: p for p in progress_records}
            else:
                # Direct course enrollment
                learning_resources = LearningResource.objects.filter(course=course).order_by('order')
                context['learning_resources'] = learning_resources
                
                # Fetch progress for learning resources
                progress_records = Progress.objects.filter(
                    enrollment=enrollment,
                    learning_resource__in=learning_resources
                )
                context['resource_progress'] = {p.learning_resource_id: p for p in progress_records}

            # Fetch overall course progress
            context['course_progress'] = Progress.objects.filter(
                enrollment=enrollment,
                course=course,
                learning_resource__isnull=True
            ).first()

            # Additional context data
            context['instructor'] = course.created_by

        except Exception as e:
            logger.error(f"Error in MyCourseDetailsView get_context_data: {str(e)}")
            context['error'] = "An error occurred while fetching course details."

        return context
    
class LearningResourceDetailView(LoginRequiredMixin, DetailView):
    model = LearningResource
    context_object_name = 'resource'
    template_name = 'users/learner/courses/learning_resource_base.html'

    def get_object(self, queryset=None):
        resource_id = self.kwargs.get('resource_id')
        try:
            return get_object_or_404(LearningResource, id=resource_id)
        except Exception as e:
            logger.error(f"Error fetching learning resource with id {resource_id}: {str(e)}", exc_info=True)
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            resource = self.object
            user = self.request.user

            # Get the enrollment for this resource
            enrollment = Enrollment.objects.filter(
                user=user,
                course=resource.course
            ).first()

            if not enrollment:
                context['error'] = "You are not enrolled in this course."
                return context

            # Get or create progress for this resource
            progress, created = Progress.objects.get_or_create(
                enrollment=enrollment,
                learning_resource=resource,
                defaults={
                    'progress_type': 'LEARNING_RESOURCE',
                    'total_items': 1  # Assuming each resource counts as one item
                }
            )

            context['enrollment'] = enrollment
            context['progress'] = progress
            context['is_completed'] = progress.completed_items == progress.total_items

            # Set the specific template based on resource type
            context['specific_template'] = f'users/learner/courses/resource_types/{resource.resource_type.lower()}_detail.html'

            # Add resource-specific context data
            if resource.resource_type == 'SCORM':
                context['scorm_details'] = resource.scorm_details
                context['SCORM_API_BASE_URL'] = settings.SCORM_API_BASE_URL
                context['SCORM_PLAYER_USER_ID'] = user.scorm_profile.scorm_player_id
                context['SCORM_PLAYER_API_TOKEN'] = user.scorm_profile.token
            elif resource.resource_type == 'QUIZ':
                context['quiz_details'] = resource.quiz
            # Add more resource-specific context as needed

        except Exception as e:
            logger.error(f"Error in LearningResourceDetailView get_context_data for user {user.id} and resource {resource.id if resource else 'None'}: {str(e)}", exc_info=True)
            context['error'] = "An error occurred while fetching resource details. Please try again later."

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