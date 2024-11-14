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
from django.db.models import Count, Avg
from django.core.cache import cache
from django.views import View
from django.template.loader import render_to_string

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from certificates.models import Certificate
from django.utils import timezone
from django.utils.translation import gettext as _
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from .models import User, SCORMUserProfile
from .forms import (
    PersonalInfoForm,
    PasswordChangeForm,
    PreferencesForm,
    ProfilePictureForm
)

from django_filters.views import FilterView
from .filters import NotificationFilter
from courses.filters import ProgramFilter, CourseFilter
from django.db.models import Prefetch
from django.db.models import Avg, Q
from django.db import models
from django.contrib.contenttypes.models import ContentType

from quizzes.models import QuizAttempt
from courses.forms import CourseForm, LearningResourceFormSet, ScormResourceForm, UserEnrollmentForm
from courses.models import (Course, CourseCategory, Enrollment, LearningResource, ScormResource, Tag, Program, ProgramCourse, Review, Progress, DeliveryComponent, Delivery, ComponentCompletion)
from .api_client import upload_scorm_package, register_user_for_course
from support.models import SupportTicket, SupportCategory
from support.forms import TicketForm
from announcements.models import Announcement, AnnouncementRecipient, AnnouncementRead

from activities.models import SystemNotification
from .utils.notification_utils import create_notification, log_activity
from .mixins import LearnerRequiredMixin

logger = logging.getLogger(__name__)

User = get_user_model()

class DashboardView(TemplateView):
    template_name = 'users/learner/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class LearningCatalogView(LearnerRequiredMixin, LoginRequiredMixin, ListView):
    template_name = 'users/learner/learning_catalog/learning_catalog.html'
    context_object_name = 'courses'
    paginate_by = 12

    def get_queryset(self):
        try:
            queryset = Course.objects.filter(is_published=True)
            search_query = self.request.GET.get('search')
            category = self.request.GET.get('category')
            level = self.request.GET.get('level')

            if search_query:
                queryset = queryset.filter(
                    Q(title__icontains=search_query) |
                    Q(description__icontains=search_query)
                )

            if category:
                queryset = queryset.filter(category__name=category)

            if level:
                queryset = queryset.filter(difficulty_level=level)

            return queryset.order_by('-created_at')
        except Exception as e:
            logger.error(f"Error in LearningCatalogView get_queryset: {str(e)}")
            return Course.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['categories'] = CourseCategory.objects.filter(status='ACTIVE')
            context['featured_programs'] = Program.objects.filter(is_published=True)[:3]
            context['total_programs'] = Program.objects.filter(is_published=True).count()
            
            # Paginate courses
            page = self.request.GET.get('page')
            paginator = Paginator(self.object_list, self.paginate_by)
            try:
                courses = paginator.page(page)
            except PageNotAnInteger:
                courses = paginator.page(1)
            except EmptyPage:
                courses = paginator.page(paginator.num_pages)
            
            context['courses'] = courses
            context['search_query'] = self.request.GET.get('search', '')
            context['selected_category'] = self.request.GET.get('category', '')
            context['selected_level'] = self.request.GET.get('level', '')
        except Exception as e:
            logger.error(f"Error in LearningCatalogView get_context_data: {str(e)}")
        return context
    
class ProgramListView(LearnerRequiredMixin, LoginRequiredMixin, ListView):
    template_name = 'users/learner/learning_catalog/program_list.html'
    context_object_name = 'programs'
    paginate_by = 12

    def get_queryset(self):
        try:
            queryset = Program.objects.filter(is_published=True)
            search_query = self.request.GET.get('search')
            
            if search_query:
                queryset = queryset.filter(
                    Q(title__icontains=search_query) |
                    Q(description__icontains=search_query)
                )

            return queryset.order_by('-created_at')
        except Exception as e:
            logger.error(f"Error in ProgramListView get_queryset: {str(e)}")
            return Program.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['search_query'] = self.request.GET.get('search', '')
        except Exception as e:
            logger.error(f"Error in ProgramListView get_context_data: {str(e)}")
        return context
    

class CourseDetailView(LearnerRequiredMixin, LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'users/learner/learning_catalog/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            course = self.get_object()
            context['learning_resources'] = LearningResource.objects.filter(course=course).order_by('order')
            context['reviews'] = Review.objects.filter(content_type__model='course', object_id=course.id)
            context['average_rating'] = context['reviews'].aggregate(Avg('rating'))['rating__avg']
            context['total_reviews'] = context['reviews'].count()
            context['is_enrolled'] = Enrollment.objects.filter(course=course, user=self.request.user).exists()
            context['total_enrollments'] = Enrollment.objects.filter(course=course).count()
            
            logger.info(f"Course detail page accessed for course {course.id} by user {self.request.user.username}")
        except Exception as e:
            logger.error(f"Error in CourseDetailView get_context_data: {str(e)}")
        return context
    
    
class ProgramDetailView(LearnerRequiredMixin, LoginRequiredMixin, DetailView):
    model = Program
    template_name = 'users/learner/learning_catalog/program_detail.html'
    context_object_name = 'program'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            program = self.get_object()
            context['program_courses'] = ProgramCourse.objects.filter(program=program).select_related('course').order_by('order')
            context['reviews'] = Review.objects.filter(content_type__model='program', object_id=program.id)
            context['average_rating'] = context['reviews'].aggregate(Avg('rating'))['rating__avg']
            context['total_reviews'] = context['reviews'].count()
            context['is_enrolled'] = Enrollment.objects.filter(program=program, user=self.request.user).exists()
            context['total_duration'] = sum([pc.course.duration for pc in context['program_courses'] if pc.course.duration])
            context['total_courses'] = context['program_courses'].count()
            context['total_enrollments'] = Enrollment.objects.filter(program=program).count()    

            # Get learning resources for each course
            for program_course in context['program_courses']:
                program_course.learning_resources = program_course.course.resources.all()

            logger.info(f"Program detail page accessed for program {program.id} by user {self.request.user.username}")
        except Exception as e:
            logger.error(f"Error in ProgramDetailView get_context_data: {str(e)}")
        return context
    


class EnrollmentsView(LearnerRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = 'users/learner/enrollments/enrollments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        try:
            # Get all enrollments for the user
            enrollments = Enrollment.objects.filter(user=user).select_related(
                'delivery', 'program', 'course'
            ).prefetch_related('progress_records')

            # Active enrollments
            active_enrollments = enrollments.filter(
                Q(status='ENROLLED') | Q(status='IN_PROGRESS')
            ).order_by('-enrollment_date')

            # Completed enrollments
            completed_enrollments = enrollments.filter(status='COMPLETED').order_by('-completion_date')

            # Calculate summary statistics
            total_enrollments = enrollments.count()
            active_count = active_enrollments.count()
            completed_count = completed_enrollments.count()

            # Get certificates
            certificates = Certificate.objects.filter(user=user)
            certificate_count = certificates.count()

            # Process active enrollments
            processed_active_enrollments = []
            for enrollment in active_enrollments:
                progress = Progress.objects.filter(enrollment=enrollment).first()
                processed_enrollment = {
                    'enrollment': enrollment,
                    'title': self.get_enrollment_title(enrollment),
                    'type': self.get_enrollment_type(enrollment),
                    'progress': progress.progress_percentage if progress else 0,
                    'start_date': enrollment.enrollment_date,
                    'estimated_completion': self.estimate_completion_date(enrollment),
                }
                processed_active_enrollments.append(processed_enrollment)

            context.update({
                'active_enrollments': processed_active_enrollments,
                'completed_enrollments': completed_enrollments,
                'total_enrollments': total_enrollments,
                'active_count': active_count,
                'completed_count': completed_count,
                'certificate_count': certificate_count,
            })

        except Exception as e:
            logger.error(f"Error in EnrollmentsView for user {user}: {str(e)}")
            context['error_message'] = "An error occurred while fetching your enrollments. Please try again later."

        return context

    def get_enrollment_title(self, enrollment):
        if enrollment.delivery:
            return enrollment.delivery.title
        elif enrollment.program:
            return enrollment.program.title
        elif enrollment.course:
            return enrollment.course.title
        return "Unknown Enrollment"

    def get_enrollment_type(self, enrollment):
        if enrollment.delivery:
            return enrollment.delivery.delivery_type
        elif enrollment.program:
            return 'PROGRAM'
        elif enrollment.course:
            return 'COURSE'
        return "UNKNOWN"

    def estimate_completion_date(self, enrollment):
        try:
            if enrollment.delivery:
                return enrollment.delivery.end_date
            # For direct enrollments, you might want to implement a more sophisticated estimation
            # based on the average completion time or the intended duration of the program/course
            return enrollment.enrollment_date + timezone.timedelta(days=90)  # Example: 3 months from enrollment
        except Exception as e:
            logger.error(f"Error estimating completion date for enrollment {enrollment.id}: {str(e)}")
            return None
        

class EnrollmentCreateView(LoginRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        try:
            enrollment_type = request.POST.get('enrollment_type')
            object_id = request.POST.get('object_id')

            if enrollment_type not in ['course', 'program']:
                raise ValueError(_("Invalid enrollment type"))

            with transaction.atomic():
                if enrollment_type == 'course':
                    course = get_object_or_404(Course, id=object_id)
                    enrollment = Enrollment.objects.create(
                        user=request.user,
                        course=course,
                        status='ENROLLED'
                    )
                    message = _("Successfully enrolled in the course: {}").format(course.title)
                else:
                    program = get_object_or_404(Program, id=object_id)
                    enrollment = Enrollment.objects.create(
                        user=request.user,
                        program=program,
                        status='ENROLLED'
                    )
                    message = _("Successfully enrolled in the program: {}").format(program.title)

                logger.info(f"User {request.user.username} enrolled in {enrollment_type} {object_id}")
                return JsonResponse({'status': 'success', 'message': message})

        except ValueError as ve:
            logger.warning(f"Invalid enrollment attempt: {str(ve)}")
            return JsonResponse({'status': 'error', 'message': str(ve)}, status=400)
        except Exception as e:
            logger.error(f"Enrollment creation failed: {str(e)}")
            return JsonResponse({'status': 'error', 'message': _("An error occurred during enrollment. Please try again.")}, status=500)
        

class CourseConsumptionView(LoginRequiredMixin, LearnerRequiredMixin, DetailView):
    template_name = 'users/learner/enrollments/course_consumption.html'
    context_object_name = 'enrollment'

    def get_object(self, queryset=None):
        try:
            enrollment_id = self.kwargs.get('enrollment_id')
            enrollment = get_object_or_404(
                Enrollment.objects.select_related(
                    'delivery', 'program', 'course', 'user'
                ).prefetch_related(
                    Prefetch('progress_records', queryset=Progress.objects.order_by('-last_updated')),
                    Prefetch('component_completions', queryset=ComponentCompletion.objects.order_by('completion_date')),
                ),
                id=enrollment_id,
                user=self.request.user
            )
            return enrollment
        except Enrollment.DoesNotExist:
            logger.error(f"Enrollment with id {enrollment_id} does not exist for user {self.request.user}")
            raise PermissionDenied(_("You do not have access to this enrollment."))
        except Exception as e:
            logger.error(f"Error fetching enrollment: {str(e)}")
            raise

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            enrollment = self.object
            content_object = enrollment.delivery or enrollment.program or enrollment.course

            # Fetch resources based on the content_object type
            if enrollment.delivery:
                resources = LearningResource.objects.filter(
                    deliverycomponent__delivery=content_object
                ).order_by('deliverycomponent__order')
            elif enrollment.program:
                resources = LearningResource.objects.filter(
                    course__programcourse__program=content_object
                ).order_by('course__programcourse__order', 'order')
            elif enrollment.course:
                resources = content_object.resources.all().order_by('order')
            else:
                raise ValueError(_("Invalid enrollment type"))

            progress = enrollment.progress_records.first()
            completed_resources = set(
                enrollment.component_completions.values_list('learning_resource_id', flat=True)
            )

            processed_resources = [
                {
                    'resource': resource,
                    'is_completed': resource.id in completed_resources,
                    'type': resource.get_resource_type_display(),
                } for resource in resources
            ]

            # Get the requested resource ID from the query parameters
            requested_resource_id = self.request.GET.get('resource')
            
            # Find the current resource based on the requested ID
            current_resource = next(
                (r for r in processed_resources if str(r['resource'].id) == requested_resource_id),
                processed_resources[0] if processed_resources else None
            )

            context.update({
                'content_object': content_object,
                'resources': processed_resources,
                'progress': progress,
                'current_resource': current_resource,
            })

            # Add SCORM-specific details if the current resource is a SCORM package
            if current_resource and current_resource['resource'].resource_type == 'SCORM':
                context.update({
                    'scorm_details': current_resource['resource'].scorm_details,
                    'SCORM_API_BASE_URL': settings.SCORM_API_BASE_URL,
                    'SCORM_PLAYER_USER_ID': self.request.user.scorm_profile.scorm_player_id,
                    'SCORM_PLAYER_API_TOKEN': self.request.user.scorm_profile.token,
                })

        except Exception as e:
            logger.error(f"Error in CourseConsumptionView for enrollment {self.object.id}: {str(e)}")
            context['error_message'] = _("An error occurred while loading the course content. Please try again later.")

        return context
    
    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            context = self.get_context_data(object=self.object)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html = render_to_string('users/learner/enrollments/course_content_player.html', context, request=request)
                return JsonResponse({'html': html})
            
            return self.render_to_response(context)
        except PermissionDenied as e:
            logger.warning(f"Permission denied for user {request.user}: {str(e)}")
            return self.handle_no_permission()
        except Exception as e:
            logger.error(f"Unexpected error in CourseConsumptionView: {str(e)}")
            return JsonResponse({'error': _("An unexpected error occurred. Please try again later.")}, status=500)
    

class ProgressView(TemplateView):
    template_name = 'users/learner/progress.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class CalendarView(TemplateView):
    template_name = 'users/learner/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class MessageListView(TemplateView):
    template_name = 'users/learner/messages.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class ResourceView(TemplateView):
    template_name = 'users/learner/resource.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class LeaderboardView(TemplateView):
    template_name = 'users/learner/leaderboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    

# ============================================================
# ======================= Settings Views =====================
# ============================================================
    
class SettingsView(LoginRequiredMixin, LearnerRequiredMixin, UserPassesTestMixin, View):
    template_name = 'users/learner/settings.html'

    def test_func(self):
        return self.request.user.groups.filter(name='learner').exists()

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied(_("You do not have permission to access this page."))
        return super().handle_no_permission()

    def get(self, request):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request):
        action = request.POST.get('action')
        if action == 'update_personal_info':
            return self.update_personal_info(request)
        elif action == 'change_password':
            return self.change_password(request)
        elif action == 'update_preferences':
            return self.update_preferences(request)
        elif action == 'update_profile_picture':
            return self.update_profile_picture(request)
        else:
            messages.error(request, _("Invalid action specified."))
            return redirect('learner_settings')

    def get_context_data(self):
        user = self.request.user
        context = {
            'personal_info_form': PersonalInfoForm(instance=user),
            'password_form': PasswordChangeForm(user),
            'preferences_form': PreferencesForm(instance=user),
            'profile_picture_form': ProfilePictureForm(instance=user),
        }
        try:
            context['scorm_profile'] = user.scorm_profile
        except SCORMUserProfile.DoesNotExist:
            context['scorm_profile'] = None
        return context

    @transaction.atomic
    def update_personal_info(self, request):
        try:
            form = PersonalInfoForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, _("Personal information updated successfully."))
                create_notification(request.user, _("Your personal information has been updated successfully."))
                log_activity(request.user, 'UPDATE', 'Updated personal information')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                create_notification(request.user, _("Failed to update personal information."), 'ERROR')
        except Exception as e:
            logger.error(f"Error updating personal info for user {request.user.username}: {str(e)}")
            messages.error(request, _("An error occurred while updating your personal information. Please try again."))
            create_notification(request.user, _("An error occurred while updating your personal information."), 'ERROR')
        return redirect('learner_settings')

    @transaction.atomic
    def change_password(self, request):
        try:
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, _("Password changed successfully."))
                create_notification(request.user, _("Your password has been changed successfully."))
                log_activity(request.user, 'CHANGE_PASSWORD', 'User changed their password')
            else:
                error_messages = []
                for field, errors in form.errors.items():
                    for error in errors:
                        error_message = f"{field}: {error}"
                        messages.error(request, error_message)
                        error_messages.append(error_message)
                create_notification(request.user, _("Failed to change password. Please check the errors and try again."), 'ERROR')
                log_activity(request.user, 'CHANGE_PASSWORD_FAILED', f"Password change failed due to: {', '.join(error_messages)}")
        except Exception as e:
            logger.error(f"Error changing password for user {request.user.username}: {str(e)}")
            messages.error(request, _("An error occurred while changing your password. Please try again."))
            create_notification(request.user, _("An error occurred while changing your password."), 'ERROR')
            log_activity(request.user, 'CHANGE_PASSWORD_ERROR', f"Password change error: {str(e)}")
        return redirect('logout')

    @transaction.atomic
    def update_preferences(self, request):
        try:
            form = PreferencesForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, _("Preferences updated successfully."))
                create_notification(request.user, _("Your preferences have been updated successfully."))
                log_activity(request.user, 'UPDATE_PREFERENCES', 'User updated their preferences')
            else:
                error_messages = []
                for field, errors in form.errors.items():
                    for error in errors:
                        error_message = f"{field}: {error}"
                        messages.error(request, error_message)
                        error_messages.append(error_message)
                create_notification(request.user, _("Failed to update preferences. Please check the errors and try again."), 'ERROR')
                log_activity(request.user, 'UPDATE_PREFERENCES_FAILED', f"Preference update failed due to: {', '.join(error_messages)}")
        except Exception as e:
            logger.error(f"Error updating preferences for user {request.user.username}: {str(e)}")
            messages.error(request, _("An error occurred while updating your preferences. Please try again."))
            create_notification(request.user, _("An error occurred while updating your preferences."), 'ERROR')
            log_activity(request.user, 'UPDATE_PREFERENCES_ERROR', f"Preference update error: {str(e)}")
        return redirect('learner_settings')

    @transaction.atomic
    def update_profile_picture(self, request):
        try:
            form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, _("Profile picture updated successfully."))
                create_notification(request.user, _("Your profile picture has been updated successfully."))
                log_activity(request.user, 'UPDATE_PROFILE_PICTURE', 'User updated their profile picture')
            else:
                error_messages = []
                for field, errors in form.errors.items():
                    for error in errors:
                        error_message = f"{field}: {error}"
                        messages.error(request, error_message)
                        error_messages.append(error_message)
                create_notification(request.user, _("Failed to update profile picture. Please check the errors and try again."), 'ERROR')
                log_activity(request.user, 'UPDATE_PROFILE_PICTURE_FAILED', f"Profile picture update failed due to: {', '.join(error_messages)}")
        except Exception as e:
            logger.error(f"Error updating profile picture for user {request.user.username}: {str(e)}")
            messages.error(request, _("An error occurred while updating your profile picture. Please try again."))
            create_notification(request.user, _("An error occurred while updating your profile picture."), 'ERROR')
            log_activity(request.user, 'UPDATE_PROFILE_PICTURE_ERROR', f"Profile picture update error: {str(e)}")
        return redirect('learner_settings')

# ============================================================
# ====================== Help & Support Views ================
# ============================================================
    
@method_decorator(login_required, name='dispatch')
class HelpSupportView(TemplateView):
    template_name = 'users/learner/support/help_and_support.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['support_tickets'] = SupportTicket.objects.filter(created_by=self.request.user)
        return context
    
class LearnerTicketCreateView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'users/learner/support/tickets/create.html'
    form_class = TicketForm
    success_url = reverse_lazy('learner_help_support')  

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Support Ticket'
        return context

    def test_func(self):
        return self.request.user.groups.filter(name='learner').exists()

    def form_valid(self, form):
        try:
            ticket = form.save(commit=False)
            ticket.created_by = self.request.user
            ticket.save()
            messages.success(self.request, 'Support ticket created successfully!')
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error creating support ticket: {e}")
            messages.error(self.request, 'There was an error creating the support ticket. Please try again later.')
            return self.form_invalid(form)

    def form_invalid(self, form):
        logger.error(f"Form errors: {form.errors}")
        messages.error(self.request, 'There was an error creating the support ticket. Please check the form and try again.')
        return super().form_invalid(form)
    
    
class LearnerTicketDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = SupportTicket
    template_name = 'users/learner/support/tickets/ticket_details.html'
    context_object_name = 'support_ticket'

    def test_func(self):
        return self.request.user.groups.filter(name='learner').exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
    
# ============================================================
# ======================= Notifications Views ================
# ============================================================

class RecentNotificationsView(LoginRequiredMixin, LearnerRequiredMixin, View):
    def get(self, request):
        notifications = SystemNotification.objects.filter(
            user=request.user,
            is_read=False
        )[:3]  

        data = [{
            'id': notification.id,
            'message': notification.message,
            'timestamp': notification.timestamp.isoformat()
        } for notification in notifications]

        return JsonResponse(data, safe=False)

class NotificationListView(FilterView, ListView):
    model = SystemNotification
    template_name = 'users/learner/notifications/notifications_list.html'
    context_object_name = 'notifications'
    filterset_class = NotificationFilter

    def get_queryset(self):
        try:
            return SystemNotification.objects.filter(user=self.request.user).order_by('-timestamp')
        except Exception as e:
            logger.error(f"Error fetching notifications for user {self.request.user}: {e}")
            return SystemNotification.objects.none()
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        return context
        
class MarkNotificationReadView(LoginRequiredMixin, LearnerRequiredMixin, View):
    def post(self, request, pk):
        try:
            notification = SystemNotification.objects.get(id=pk, user=request.user)
            notification.is_read = True
            notification.save()
            return redirect('learner_notifications')
        except SystemNotification.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return JsonResponse({'status': 'error', 'message': 'An error occurred'}, status=500)

class MarkAllNotificationsReadView(LoginRequiredMixin, LearnerRequiredMixin, View):
    def post(self, request):
        SystemNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    
class UnreadNotificationsCountView(LoginRequiredMixin, LearnerRequiredMixin, View):
    def get(self, request):
        try:
            count = SystemNotification.objects.filter(user=request.user, is_read=False).count()
            return JsonResponse({'count': count})
        except Exception as e:
            logger.error(f"Error fetching unread notifications count for user {request.user}: {e}")
            return JsonResponse({'count': 0})
        

# ============================================================
# =================== Announcements Views ====================
# ============================================================

class AnnouncementListView(LearnerRequiredMixin, LoginRequiredMixin, ListView):
    model = Announcement
    template_name = 'users/learner/announcements/announcement_page.html'
    context_object_name = 'announcements'

    def get_queryset(self):
        user = self.request.user
        queryset = Announcement.objects.filter(
            is_active=True
        ).prefetch_related('recipients').order_by('-publish_date')

        # Filter announcements based on recipient types and user access
        user_announcements = queryset.filter(
            models.Q(recipients__recipient_type='ALL') |
            models.Q(recipients__recipient_type='STUDENTS') |
            models.Q(
                recipients__recipient_type='USER',
                recipients__content_type=ContentType.objects.get_for_model(User),
                recipients__object_id=user.id
            )
        ).distinct()

        return user_announcements

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context if needed
        return context

class AnnouncementDetailView(LearnerRequiredMixin, LoginRequiredMixin, DetailView):
    model = Announcement
    template_name = 'users/learner/announcements/announcement_detail.html'
    context_object_name = 'announcement'

    def get_queryset(self):
        return Announcement.objects.filter(id=self.kwargs.get('pk'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        announcement = self.get_object()
        announcement_read = AnnouncementRead.objects.filter(user=self.request.user, announcement=announcement).first()
        context['announcement_read'] = announcement_read
        return context
    
class AnnouncementReadView(LearnerRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            announcement = Announcement.objects.get(id=pk)
            announcement_read, created = AnnouncementRead.objects.get_or_create(user=self.request.user, announcement=announcement)
            if created:
                logger.info(f"Announcement {pk} marked as read by user {request.user.id}")
            else:
                logger.info(f"Announcement {pk} was already marked as read by user {request.user.id}")
            return JsonResponse({'status': 'success'})
        except Announcement.DoesNotExist:
            logger.warning(f"Announcement {pk} not found for user {request.user.id}")
            return JsonResponse({'status': 'error', 'message': 'Announcement not found'}, status=404)
        except Exception as e:
            logger.error(f"Error marking announcement {pk} as read for user {request.user.id}: {e}")
            return JsonResponse({'status': 'error', 'message': 'An error occurred'}, status=500)

