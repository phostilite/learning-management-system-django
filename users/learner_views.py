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
from django.utils.translation import gettext as _
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.contrib.auth import get_user_model

from django_filters.views import FilterView
from .filters import ProgramFilter, CourseFilter
from django.db.models import Prefetch
from django.db.models import Avg, Q


from courses.forms import CourseForm, LearningResourceFormSet, ScormResourceForm, UserEnrollmentForm
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
    

class MyProgramListView(LoginRequiredMixin, ListView):
    template_name = 'users/learner/programs/my_programs.html'
    context_object_name = 'enrollments'

    def get_queryset(self):
        try:
            user = self.request.user
            enrollments = Enrollment.objects.filter(user=user).select_related('program', 'delivery')
            
            enrollment_data = []
            for enrollment in enrollments:
                if enrollment.delivery and enrollment.delivery.delivery_type == 'PROGRAM':
                    title = enrollment.delivery.title
                    enrollment_type = 'Via Delivery'
                elif enrollment.program:
                    title = enrollment.program.title
                    enrollment_type = 'Direct'
                else:
                    logger.error(f"Enrollment {enrollment.id} has no associated delivery or program")
                    continue
                
                enrollment_data.append({
                    'id': enrollment.id,
                    'title': title,
                    'enrollment_type': enrollment_type,
                    'status': enrollment.status,
                })
            
            logger.info(f"Retrieved {len(enrollment_data)} program enrollments for user {user.username}")
            return enrollment_data
        except Exception as e:
            logger.error(f"Error retrieving program enrollments for user {user.username}: {str(e)}")
            raise

class MyProgramDetailView(LoginRequiredMixin, DetailView):
    template_name = 'users/learner/programs/my_program_detail.html'
    context_object_name = 'enrollment'

    def get_object(self):
        enrollment_id = self.kwargs.get('enrollment_id')
        user = self.request.user
        return get_object_or_404(Enrollment, id=enrollment_id, user=user)

    def get_template_names(self):
        enrollment = self.get_object()
        if enrollment.delivery:
            return ['users/learner/programs/my_program_detail_delivery.html']
        else:
            return ['users/learner/programs/my_program_detail_direct.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enrollment = self.get_object()

        try:
            if enrollment.delivery:
                # Delivery enrollment
                delivery = enrollment.delivery
                components = DeliveryComponent.objects.filter(delivery=delivery).select_related(
                    'program_course__course', 'learning_resource'
                ).order_by('order')

                context['delivery'] = delivery
                context['components'] = components
                logger.info(f"Retrieved {components.count()} delivery components for enrollment {enrollment.id}")
            else:
                # Direct program enrollment
                program = enrollment.program
                program_courses = program.program_courses.select_related('course').order_by('order')
                courses_with_resources = []

                for program_course in program_courses:
                    course = program_course.course
                    resources = LearningResource.objects.filter(course=course).order_by('order')
                    courses_with_resources.append({
                        'course': course,
                        'resources': resources
                    })

                context['program'] = program
                context['courses_with_resources'] = courses_with_resources
                logger.info(f"Retrieved {len(courses_with_resources)} courses with resources for enrollment {enrollment.id}")

        except Exception as e:
            logger.error(f"Error retrieving details for enrollment {enrollment.id}: {str(e)}")
            raise

        return context
    
class DirectCourseConsumptionView(LoginRequiredMixin, DetailView):
    template_name = 'users/learner/programs/course_consumption/direct/course_consumption.html'
    context_object_name = 'program_course'

    def get_object(self):
        try:
            enrollment_id = self.kwargs.get('enrollment_id')
            course_id = self.kwargs.get('course_id')
            user = self.request.user

            enrollment = get_object_or_404(Enrollment, id=enrollment_id, user=user)
            program_course = get_object_or_404(ProgramCourse, program=enrollment.program, course__id=course_id)

            return program_course
        except Exception as e:
            logger.error(f"Error retrieving program course for user {self.request.user.username}: {str(e)}")
            raise

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            program_course = self.object
            resources = LearningResource.objects.filter(course=program_course.course).order_by('order')
            context['resources'] = resources
            context['enrollment_id'] = self.kwargs.get('enrollment_id')
            logger.info(f"Retrieved {resources.count()} learning resources for course {program_course.course.id}")
        except Exception as e:
            logger.error(f"Error retrieving learning resources for course {program_course.course.id}: {str(e)}")
            raise
        return context
    
class DirectResourceConsumptionView(LoginRequiredMixin, DetailView):
    template_name = 'users/learner/programs/course_consumption/direct/resource_types/resource_consumption.html'
    context_object_name = 'resource'

    def get_object(self):
        try:
            resource_id = self.kwargs.get('resource_id')
            # Directly retrieve the resource without re-validating the enrollment
            resource = get_object_or_404(LearningResource, id=resource_id)
            return resource
        except Exception as e:
            logger.error(f"Error retrieving learning resource for user {self.request.user.username}: {str(e)}")
            raise

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enrollment_id'] = self.kwargs.get('enrollment_id')

        # Add SCORM-specific context if the resource type is SCORM
        if self.object.resource_type == 'SCORM':
            context['scorm_details'] = self.object.scorm_details
            context['SCORM_API_BASE_URL'] = settings.SCORM_API_BASE_URL
            context['SCORM_PLAYER_USER_ID'] = self.request.user.scorm_profile.scorm_player_id
            context['SCORM_PLAYER_API_TOKEN'] = self.request.user.scorm_profile.token

        return context

    def get_template_names(self):
        resource = self.object
        return [
            f'users/learner/programs/course_consumption/direct/resource_types/{resource.resource_type.lower()}_resource.html',
            self.template_name
        ]
    
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
    
class MyCourseListView(LoginRequiredMixin, ListView):
    template_name = 'users/learner/courses/my_courses.html'
    context_object_name = 'enrollments'

    def get_queryset(self):
        try:
            user = self.request.user
            enrollments = Enrollment.objects.filter(user=user).select_related('course', 'delivery')
            
            enrollment_data = []
            for enrollment in enrollments:
                if enrollment.delivery and enrollment.delivery.delivery_type == 'COURSE':
                    title = enrollment.delivery.title
                    enrollment_type = 'Via Delivery'
                elif enrollment.course:
                    title = enrollment.course.title
                    enrollment_type = 'Direct'
                else:
                    logger.error(f"Enrollment {enrollment.id} has no associated delivery or course")
                    continue
                
                enrollment_data.append({
                    'id': enrollment.id,
                    'title': title,
                    'enrollment_type': enrollment_type,
                    'status': enrollment.status,
                })
            
            logger.info(f"Retrieved {len(enrollment_data)} course enrollments for user {user.username}")
            return enrollment_data
        except Exception as e:
            logger.error(f"Error retrieving course enrollments for user {user.username}: {str(e)}")
            raise

class MyCourseDetailView(LoginRequiredMixin, DetailView):
    template_name = 'users/learner/courses/my_course_detail.html'
    context_object_name = 'enrollment'

    def get_object(self):
        enrollment_id = self.kwargs.get('enrollment_id')
        user = self.request.user
        return get_object_or_404(Enrollment, id=enrollment_id, user=user)

    def get_template_names(self):
        enrollment = self.get_object()
        if enrollment.delivery:
            return ['users/learner/courses/my_course_detail_delivery.html']
        else:
            return ['users/learner/courses/my_course_detail_direct.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enrollment = self.get_object()

        try:
            if enrollment.delivery:
                # Delivery enrollment
                delivery = enrollment.delivery
                components = DeliveryComponent.objects.filter(delivery=delivery).select_related(
                    'learning_resource'
                ).order_by('order')

                context['delivery'] = delivery
                context['components'] = components
                logger.info(f"Retrieved {components.count()} delivery components for enrollment {enrollment.id}")
            else:
                # Direct course enrollment
                course = enrollment.course
                resources = LearningResource.objects.filter(course=course).order_by('order')

                context['course'] = course
                context['resources'] = resources
                logger.info(f"Retrieved {resources.count()} resources for enrollment {enrollment.id}")

        except Exception as e:
            logger.error(f"Error retrieving details for enrollment {enrollment.id}: {str(e)}")
            raise

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
    

# ================================================================
#                           Enrollment Views
# ================================================================

class EnrollmentConfirmationView(LoginRequiredMixin, FormView):
    template_name = 'users/learner/enrollment/enrollment_confirmation.html'
    form_class = UserEnrollmentForm
    success_url = reverse_lazy('learner_dashboard')

    def get_initial(self):
        return {
            'enrollment_type': self.kwargs['enrollment_type'],
            'object_id': self.kwargs['object_id']
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enrollment_type = self.kwargs['enrollment_type']
        object_id = self.kwargs['object_id']

        logger.info(f"EnrollmentConfirmationView: get_context_data called for {enrollment_type} with id {object_id}")

        try:
            if enrollment_type == 'program':
                context['object'] = get_object_or_404(Program, id=object_id)
                logger.info(f"Program found: {context['object'].title}")
            elif enrollment_type == 'course':
                context['object'] = get_object_or_404(Course, id=object_id)
                logger.info(f"Course found: {context['object'].title}")
            else:
                logger.error(f"Invalid enrollment type: {enrollment_type}")
                raise ValueError("Invalid enrollment type")
        except Exception as e:
            logger.error(f"Error in EnrollmentConfirmationView get_context_data: {str(e)}")
            messages.error(self.request, _("An error occurred. Please try again."))
            return redirect('home')

        return context

    def form_valid(self, form):
        enrollment_type = form.cleaned_data['enrollment_type']
        object_id = form.cleaned_data['object_id']

        logger.info(f"EnrollmentConfirmationView: form_valid called for {enrollment_type} with id {object_id}")

        try:
            with transaction.atomic():
                if enrollment_type == 'program':
                    program = get_object_or_404(Program, id=object_id)
                    logger.info(f"Program found: {program.title}")

                    enrollment, created = Enrollment.objects.get_or_create(
                        user=self.request.user,
                        program=program,
                        defaults={'status': 'ENROLLED'}
                    )

                else:  # course
                    course = get_object_or_404(Course, id=object_id)
                    logger.info(f"Course found: {course.title}")


                    enrollment, created = Enrollment.objects.get_or_create(
                        user=self.request.user,
                        course=course,
                        defaults={'status': 'ENROLLED'}
                    )

                if created:
                    logger.info(f"New enrollment created: {enrollment.id}")
                    messages.success(self.request, _("You have successfully enrolled."))
                else:
                    logger.info(f"Existing enrollment found: {enrollment.id}")
                    messages.info(self.request, _("You were already enrolled."))

                logger.info(f"Enrollment process completed successfully for user {self.request.user.username}")

        except Exception as e:
            logger.exception(f"Error in EnrollmentConfirmationView form_valid: {str(e)}")
            messages.error(self.request, _("An error occurred during enrollment. Please try again."))
            return JsonResponse({'error': 'An error occurred during enrollment.'}, status=500)

        return super().form_valid(form)

    def form_invalid(self, form):
        logger.warning(f"Invalid form submission: {form.errors}")
        messages.error(self.request, _("Invalid enrollment data. Please try again."))
        return super().form_invalid(form)

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