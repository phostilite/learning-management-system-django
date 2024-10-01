# Standard library imports
import json
import logging
from datetime import timedelta

# Third-party imports
import requests
from formtools.wizard.views import SessionWizardView
from rest_framework import permissions, status
from rest_framework.permissions import BasePermission, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.views import FilterView

# Django imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.forms import formset_factory
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import (CreateView, DeleteView, DetailView, FormView,
                                  ListView, TemplateView, UpdateView)

# Local application imports
from .api_client import (create_scormhub_course, register_user_for_course,
                         upload_scorm_package)
from .mixins import AdministratorRequiredMixin
from certificates.models import Certificate
from courses.forms import (CourseComponentForm, CourseForm, CoursePublishForm,
                           CourseUnpublishForm, DeliveryCreateForm,
                           DeliveryEditForm, EnrollmentEditForm,
                           EnrollmentForm, LearningResourceEditForm,
                           LearningResourceForm, LearningResourceFormSet,
                           ProgramCourseForm, ProgramForm, ProgramPublishForm,
                           ProgramUnpublishForm, ResourceComponentForm,
                           ScormResourceForm)
from courses.models import (Course, CourseCategory, Delivery, DeliveryComponent,
                            Enrollment, LearningResource, Program,
                            ProgramCourse, ScormResource, Tag)
from organization.models import Organization, OrganizationUnit, OrganizationContact, OrganizationChange, Location, JobPosition, EmployeeProfile
from organization.forms import EmployeeProfileForm, JobPositionForm, LocationForm, OrganizationUnitForm, OrganizationGroupForm
from quizzes.forms import ChoiceForm, ChoiceFormSet, QuestionForm, QuestionFormSet, QuizForm
from quizzes.models import Choice, Question, Quiz
from users.forms import LearnerCreationForm
from users.models import SCORMUserProfile, User
from activities.models import SystemNotification, ActivityLog, UserSession

from .utils.notification_utils import create_notification, log_activity
from .filters import NotificationFilter, EmployeeProfileFilter, OrganizationUnitFilter, JobPositionFilter, LocationFilter, GroupFilter, DeliveryFilter, EnrollmentFilter, UserFilter

# Initialize logger
logger = logging.getLogger(__name__)

# Get the user model
User = get_user_model()


class AdministratorDashboardView(LoginRequiredMixin, AdministratorRequiredMixin, TemplateView):
    template_name = 'users/administrator/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class AdministratorCalendarView(LoginRequiredMixin, AdministratorRequiredMixin, TemplateView):
    template_name = 'users/administrator/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class AdministratorLeaderboardView(LoginRequiredMixin, AdministratorRequiredMixin, TemplateView):
    template_name = 'users/administrator/leaderboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class AdministratorCertificateListView(LoginRequiredMixin, AdministratorRequiredMixin, ListView):
    template_name = 'users/administrator/certificates.html'
    model = Certificate
    context_object_name = 'certificates'

    def get_queryset(self):
        queryset = Certificate.objects.select_related(
            'learner__user', 'course', 'course_delivery'
        ).order_by('-issue_date')

        course_filter = self.request.GET.get('course')
        if course_filter and course_filter != 'all':
            queryset = queryset.filter(course__id=course_filter)

        date_filter = self.request.GET.get('date_range', 'last_30_days')
        if date_filter == 'last_30_days':
            queryset = queryset.filter(issue_date__gte=timezone.now() - timedelta(days=30))
        elif date_filter == 'last_3_months':
            queryset = queryset.filter(issue_date__gte=timezone.now() - timedelta(days=90))
        elif date_filter == 'this_year':
            queryset = queryset.filter(issue_date__year=timezone.now().year)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Efficient certificate statistics
        total_certificates = Certificate.objects.count()
        certificates_this_month = Certificate.objects.filter(
            issue_date__month=timezone.now().month,
            issue_date__year=timezone.now().year
        ).count()
        pending_approvals = Certificate.objects.filter(is_valid=False).count()
        courses_with_certificates = Course.objects.filter(certificates__isnull=False).distinct().count()

        context.update({
            'total_certificates': total_certificates,
            'certificates_this_month': certificates_this_month,
            'pending_approvals': pending_approvals,
            'courses_with_certificates': courses_with_certificates,
        })

        # All courses with certificates
        context['courses'] = Course.objects.filter(certificates__isnull=False).distinct().annotate(
            certificate_count=Count('certificates')
        ).order_by('title')

        # Efficient course categories for filtering
        context['course_categories'] = CourseCategory.objects.annotate(
            certificate_count=Count('course__certificates')
        ).filter(certificate_count__gt=0)

        # Selected filters
        context['selected_course'] = self.request.GET.get('course', 'all')
        context['selected_date_range'] = self.request.GET.get('date_range', 'last_30_days')

        # Generate report data (example: certificates per month)
        report_data = Certificate.objects.annotate(
            month=TruncMonth('issue_date')
        ).values('month').annotate(count=Count('id')).order_by('month')
        context['report_data'] = list(report_data)

        return context
    
class AdministratorAnnouncementListView(LoginRequiredMixin, AdministratorRequiredMixin, TemplateView):
    template_name = 'users/administrator/announcements.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class AdministratorHelpSupportView(LoginRequiredMixin, AdministratorRequiredMixin, TemplateView):
    template_name = 'users/administrator/help_support.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class AdministratorMessageListView(LoginRequiredMixin, AdministratorRequiredMixin, TemplateView):
    template_name = 'users/administrator/messages.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class AdministratorSettingsView(LoginRequiredMixin, AdministratorRequiredMixin, TemplateView):
    template_name = 'users/administrator/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    
class AdministratorLearningPathListView(LoginRequiredMixin, AdministratorRequiredMixin, TemplateView):
    template_name = 'users/administrator/course/learning_path.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class AdministratorCourseCompletionReportView(LoginRequiredMixin, AdministratorRequiredMixin, TemplateView):
    template_name = 'users/administrator/reports/course_completion.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class AdministratorUserProgressReportView(LoginRequiredMixin, AdministratorRequiredMixin, TemplateView):
    template_name = 'users/administrator/reports/user_progress.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class AdministratorAssessmentResultsReportView(LoginRequiredMixin, AdministratorRequiredMixin, TemplateView):
    template_name = 'users/administrator/reports/assessment_results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class AdministratorUserEngagementReportView(LoginRequiredMixin, AdministratorRequiredMixin, TemplateView):
    template_name = 'users/administrator/reports/user_engagement.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class AdministratorResourceUsageReportView(LoginRequiredMixin, AdministratorRequiredMixin, TemplateView):
    template_name = 'users/administrator/reports/resource_usage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class AdministratorCertificationTrackingReportView(LoginRequiredMixin, AdministratorRequiredMixin, TemplateView):
    template_name = 'users/administrator/reports/certification_tracking.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class AdministratorLearnerFeedbackReportView(LoginRequiredMixin, AdministratorRequiredMixin, TemplateView):
    template_name = 'users/administrator/reports/learner_feedback.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class AdministratorCustomReportView(LoginRequiredMixin, AdministratorRequiredMixin, TemplateView):
    template_name = 'users/administrator/reports/custom_reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class AdministratorLearnerListView(LoginRequiredMixin, AdministratorRequiredMixin, ListView):
    template_name = 'users/administrator/learners.html'
    context_object_name = 'learners'

    def get_queryset(self):
        return User.objects.filter(groups__name='learner')
    
    def post(self, request, *args, **kwargs):
        logger.info("Received request to create learner")
        try:
            data = request.POST
            logger.info("Request body parsed successfully")

            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data['firstName'],
                last_name=data['lastName']
            )
            logger.info(f"User created: {user.username}")

            learner_group, created = Group.objects.get_or_create(name='learner')
            user.groups.add(learner_group)
            logger.info(f"User added to group: learner")

            scorm_api_url = f"{settings.SCORM_API_BASE_URL}/api/users/"
            scorm_data = {
                'username': user.username,
                'password': data['password'],
                'email': user.email
            }
            response = requests.post(scorm_api_url, data=scorm_data)
            logger.info(f"SCORM API request sent: {scorm_api_url}")

            if response.status_code == 201:
                scorm_data = response.json()
                
                # Create SCORMUserProfile
                SCORMUserProfile.objects.create(
                    user=user,
                    scorm_player_id=scorm_data['user']['id'],
                    token=scorm_data['token']
                )
                logger.info(f"SCORMUserProfile created with SCORM player ID: {scorm_data['user']['id']}")
                
                return redirect('administrator_learner_list')
            else:
                user.delete()
                logger.error("Failed to create user in SCORM system")
                return JsonResponse({
                    'success': False,
                    'message': "Failed to create user in SCORM system. Please try again."
                }, status=400)

        except KeyError as e:
            logger.error(f"Missing required field: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f"Missing required field: {str(e)}"
            }, status=400)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return JsonResponse({
                'success': False,
                'message': "Invalid JSON in request body"
            }, status=400)
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)


class AdministratorFacilitatorListView(LoginRequiredMixin, AdministratorRequiredMixin, ListView):
    template_name = 'users/administrator/facilitators.html'
    context_object_name = 'facilitators'

    def get_queryset(self):
        return User.objects.filter(groups__name='facilitator')
    
    def post(self, request, *args, **kwargs):
        logger.info("Received request to create facilitator")
        try:
            data = request.POST
            logger.info("Request body parsed successfully")

            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data['firstName'],
                last_name=data['lastName']
            )
            logger.info(f"User created: {user.username}")

            facilitator_group, created = Group.objects.get_or_create(name='facilitator')
            user.groups.add(facilitator_group)
            logger.info(f"User added to group: facilitator")
            return redirect('administrator_facilitator_list')  

        except KeyError as e:
            logger.error(f"Missing required field: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f"Missing required field: {str(e)}"
            }, status=400)
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    

class AdministratorSupervisorListView(LoginRequiredMixin, AdministratorRequiredMixin, ListView):
    template_name = 'users/administrator/supervisors.html'
    context_object_name = 'supervisors'

    def get_queryset(self):
        return User.objects.filter(groups__name='supervisor')   
    
    def post(self, request, *args, **kwargs):
        logger.info("Received request to create supervisor")
        try:
            data = request.POST
            logger.info("Request body parsed successfully")

            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data['firstName'],
                last_name=data['lastName']
            )
            logger.info(f"User created: {user.username}")

            supervisor_group, created = Group.objects.get_or_create(name='supervisor')
            user.groups.add(supervisor_group)
            logger.info(f"User added to group: supervisor")

            return redirect('administrator_supervisor_list')  

        except KeyError as e:
            logger.error(f"Missing required field: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f"Missing required field: {str(e)}"
            }, status=400)
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
        
# ============================================================
# ============== Course Category Views =======================
# ============================================================

class AdministratorCourseCategoryListView(LoginRequiredMixin, AdministratorRequiredMixin, ListView):
    model = CourseCategory
    template_name = 'users/administrator/course/course_categories/categories.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return CourseCategory.objects.annotate(course_count=Count('course')).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = CourseCategory.STATUS_CHOICES
        return context


# ============================================================
# ======================= Course Views =======================
# ============================================================

class AdministratorCourseCreateView(LoginRequiredMixin, AdministratorRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'users/administrator/course/course_create.html'
    success_url = reverse_lazy('administrator_course_list') 

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class AdministratorCourseListView(LoginRequiredMixin, AdministratorRequiredMixin, ListView):
    template_name = 'users/administrator/course/course_list.html'
    context_object_name = 'courses'

    def get_queryset(self):
        try:
            courses = Course.objects.all().select_related('category')
            logger.info(f"Fetched {len(courses)} courses for user {self.request.user.id}")
            return courses
        except Exception as e:
            logger.exception("Error fetching course list:")
            messages.error(self.request, f"An error occurred while fetching the course list: {str(e)}")
            return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Fetch course metrics efficiently
        course_metrics = Course.objects.all().aggregate(
            total_courses=Count('id'),
            published_courses=Count('id', filter=Q(is_published=True)),
            unpublished_courses=Count('id', filter=Q(is_published=False))
        )
        
        # Fetch category metrics
        category_metrics = CourseCategory.objects.all().annotate(course_count=Count('course')).order_by('-course_count')[:5]

        all_categories = CourseCategory.objects.all().order_by('name')

        context.update({
            'total_courses': course_metrics['total_courses'],
            'published_courses': course_metrics['published_courses'],
            'unpublished_courses': course_metrics['unpublished_courses'],
            'top_categories': category_metrics,
            'all_categories': all_categories,
        })
        
        return context


class AdministratorCourseDetailView(LoginRequiredMixin, AdministratorRequiredMixin, DetailView):
    model = Course
    template_name = 'users/administrator/course/course_detail.html'
    context_object_name = 'course'

    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['learning_resources'] = LearningResource.objects.filter(course=self.object).order_by('order')
        
        # Count enrollments
        enrollments = Enrollment.objects.filter(course=self.object) | Enrollment.objects.filter(delivery__course=self.object)
        context['total_enrollments'] = enrollments.count()
        
        # Calculate completion rate
        completed_enrollments = enrollments.filter(status='COMPLETED').count()
        context['completion_rate'] = (completed_enrollments / context['total_enrollments'] * 100) if context['total_enrollments'] > 0 else 0
        
        # Get recent enrollments
        context['recent_enrollments'] = enrollments.order_by('-enrollment_date')[:5]
        
        return context


class AdministratorCourseEditView(LoginRequiredMixin, AdministratorRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'users/administrator/course/course_edit.html'

    def get_success_url(self):
        return reverse_lazy('administrator_course_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.object
        context['tags'] = Tag.objects.all()
        return context
    
    
class AdministratorCoursePublishView(LoginRequiredMixin, AdministratorRequiredMixin, FormView):
    template_name = 'users/administrator/course/course_publish_confirm.html'
    form_class = CoursePublishForm
    success_url = reverse_lazy('administrator_course_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['course'] = get_object_or_404(Course, pk=self.kwargs['pk'])
        return kwargs

    def form_valid(self, form):
        course = form.save()
        messages.success(self.request, f'Course "{course.title}" has been published.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, pk=self.kwargs['pk'])
        return context
    
class AdministratorCourseUnpublishView(LoginRequiredMixin, AdministratorRequiredMixin, FormView):
    template_name = 'users/administrator/course/course_unpublish_confirm.html'
    form_class = CourseUnpublishForm
    success_url = reverse_lazy('administrator_course_list')    

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['course'] = get_object_or_404(Course, pk=self.kwargs['pk'])
        return kwargs

    def form_valid(self, form):
        course = form.save()
        messages.success(self.request, f'Course "{course.title}" has been unpublished.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, pk=self.kwargs['pk'])
        return context

    

class AdministratorCourseDeleteView(LoginRequiredMixin, AdministratorRequiredMixin, DeleteView):
    model = Course
    template_name = 'users/administrator/course/course_delete_confirm.html'
    success_url = reverse_lazy('administrator_course_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, ("The course was successfully deleted."))
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = ("Delete Course")
        return context


class CourseDeliveryListView(LoginRequiredMixin, AdministratorRequiredMixin, ListView):
    template_name = 'users/administrator/course/course_delivery_list.html'
    context_object_name = 'deliveries'
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        try:
            self.course = get_object_or_404(Course, id=self.kwargs['course_id'])
            return super().dispatch(request, *args, **kwargs)
        except Http404:
            messages.error(self.request, _("The specified course does not exist."))
            return redirect('administrator_course_list')
        except Exception as e:
            logger.exception(f"Error in AdministratorCourseDeliveryListView dispatch: {str(e)}")
            messages.error(self.request, _("An unexpected error occurred. Please try again later."))
            return redirect('administrator_course_list')

    def get_queryset(self):
        try:
            return Delivery.objects.filter(course=self.course).select_related('created_by').order_by('-start_date')
        except Exception as e:
            logger.exception(f"Error fetching deliveries for course {self.course.id}: {str(e)}")
            messages.error(self.request, _("An error occurred while fetching the delivery list. Please try again."))
            return Delivery.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['course'] = self.course

            # Delivery metrics
            delivery_metrics = self.get_queryset().aggregate(
                total_deliveries=Count('id'),
                active_deliveries=Count('id', filter=Q(is_active=True)),
                completed_deliveries=Count('id', filter=Q(end_date__lt=timezone.now()))
            )

            # Enrollment metrics
            enrollment_metrics = Enrollment.objects.filter(delivery__course=self.course).aggregate(
                total_enrollments=Count('id'),
                active_enrollments=Count('id', filter=Q(status='IN_PROGRESS')),
                completed_enrollments=Count('id', filter=Q(status='COMPLETED'))
            )

            context.update({
                'delivery_metrics': delivery_metrics,
                'enrollment_metrics': enrollment_metrics,
            })

        except Exception as e:
            logger.exception(f"Error in AdministratorCourseDeliveryListView get_context_data: {str(e)}")
            messages.error(self.request, _("An error occurred while preparing the page. Some information may be missing."))

        return context
    
# ============================================================
# =================== Course Enrollment Views ================
# ============================================================

class AdministratorEnrollmentListView(LoginRequiredMixin, AdministratorRequiredMixin, ListView):
    model = Enrollment
    template_name = 'users/administrator/course/enrollments/enrollments.html'
    context_object_name = 'enrollments'

    def get_queryset(self):
        return Enrollment.objects.all().order_by('-enrollment_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate metrics
        total_enrollments = Enrollment.objects.count()
        active_enrollments = Enrollment.objects.filter(
            Q(status='ENROLLED') | Q(status='IN_PROGRESS')
        ).count()
        completed_courses = Enrollment.objects.filter(status='COMPLETED').count()

        all_courses = Course.objects.all().order_by('title')
        
        context.update({
            'total_enrollments': total_enrollments,
            'active_enrollments': active_enrollments,
            'completed_courses': completed_courses,
            'all_courses': all_courses,
        })
        
        return context
    
    
# ============================================================
# =========== Course Learning Resources Views ================
# ============================================================

class AdministratorLearningResourcesListView(LoginRequiredMixin, AdministratorRequiredMixin, ListView):
    model = LearningResource
    template_name = 'users/administrator/course/learning_resource/learning_resource_list.html'
    context_object_name = 'learning_resources'

    def get_queryset(self):
        self.course = get_object_or_404(Course, id=self.kwargs['course_id'])
        return LearningResource.objects.filter(course=self.course)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.course
        return context
    
class AdministratorLearningResourceCreateView(LoginRequiredMixin, AdministratorRequiredMixin, CreateView):
    model = LearningResource
    form_class = LearningResourceForm
    template_name = 'users/administrator/course/learning_resource/learning_resource_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, pk=self.kwargs['course_id'])
        context['scorm_upload_url'] = reverse_lazy('scorm_upload')
        return context

    @transaction.atomic
    def form_valid(self, form):
        course = get_object_or_404(Course, pk=self.kwargs['course_id'])
        form.instance.course = course

        if form.instance.resource_type == 'SCORM':
            # For SCORM resources, we'll handle the creation in the template via AJAX
            return JsonResponse({'success': True, 'redirect_url': self.get_success_url()})
        else:
            try:
                # For non-SCORM resources, save the form and handle file upload
                self.object = form.save(commit=False)
                if form.instance.resource_type in ['VIDEO', 'DOCUMENT']:
                    self.object.content = form.cleaned_data['content']
                self.object.save()
                logger.info(f"Created {form.instance.resource_type} learning resource: {self.object.id}")

                # Redirect to quiz creation if the resource type is 'QUIZ'
                if form.instance.resource_type == 'QUIZ':
                    return redirect('administrator_quiz_create', course_id=course.id, resource_id=self.object.id)

                return super().form_valid(form)
            except Exception as e:
                logger.exception(f"Error creating learning resource: {str(e)}")
                return JsonResponse({'success': False, 'error': 'An error occurred while creating the resource'}, status=500)

    def get_success_url(self):
        return reverse_lazy('administrator_course_detail', kwargs={'pk': self.kwargs['course_id']})

@require_POST
@login_required
def scorm_upload_view(request):
    try:
        action = request.POST.get('action')
        if action == 'create_course':
            title = request.POST.get('title')
            description = request.POST.get('description')
            if not all([title, description]):
                raise ValueError("Title and description are required")

            # Create SCORMHub course
            scormhub_course_id = create_scormhub_course(title, description)
            return JsonResponse({'success': True, 'scormhub_course_id': scormhub_course_id})

        elif action == 'upload_package':
            scormhub_course_id = request.POST.get('scormhub_course_id')
            lms_course_id = request.POST.get('lms_course_id')
            scorm_file = request.FILES.get('scorm_file')
            scorm_version = request.POST.get('scorm_version')

            if not all([scormhub_course_id, lms_course_id, scorm_file, scorm_version]):
                raise ValueError("All fields are required for package upload")

            # Upload SCORM package
            api_response = upload_scorm_package(scormhub_course_id, scorm_file)

            if isinstance(api_response, dict) and 'id' in api_response:
                # Create LearningResource
                course = get_object_or_404(Course, id=lms_course_id)
                resource = LearningResource.objects.create(
                    course=course,
                    title=request.POST.get('title'),
                    description=request.POST.get('description'),
                    resource_type='SCORM',
                    order=LearningResource.objects.filter(course=course).count() + 1,
                    is_mandatory=True  # You can make this configurable if needed
                )

                # Create ScormResource
                ScormResource.objects.create(
                    learning_resource=resource,
                    scorm_course_id=scormhub_course_id,
                    scorm_package_id=api_response['id'],
                    version=scorm_version,
                    web_path=api_response.get('launch_path', '')
                )

                return JsonResponse({'success': True, 'message': 'SCORM resource created successfully'})
            else:
                error_message = api_response.get('error', 'Unexpected API response format')
                raise Exception(f"Failed to create SCORM course: {error_message}")

        else:
            raise ValueError("Invalid action")

    except Exception as e:
        logger.exception("Error in SCORM upload process:")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    

class AdministratorLearningResourceEditView(LoginRequiredMixin, AdministratorRequiredMixin, UpdateView):
    model = LearningResource
    form_class = LearningResourceEditForm
    template_name = 'users/administrator/course/learning_resource/learning_resource_edit.html'
    pk_url_kwarg = 'resource_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, id=self.kwargs['course_id'])
        return context

    def get_success_url(self):
        return reverse_lazy('administrator_course_detail', kwargs={'pk': self.kwargs['course_id']})
    

class AdministratorLearningResourceDeleteView(LoginRequiredMixin, AdministratorRequiredMixin, DeleteView):
    model = LearningResource
    template_name = 'users/administrator/course/learning_resource/learning_resource_delete_confirm.html'
    pk_url_kwarg = 'resource_id'
    context_object_name = 'learning_resource'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, id=self.kwargs['course_id'])
        return context

    def get_success_url(self):
        messages.success(self.request, ("The learning resource was successfully deleted."))
        return reverse_lazy('administrator_course_detail', kwargs={'pk': self.kwargs['course_id']})

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, ("The learning resource was successfully deleted."))
        return response

class AdministratorLearningResourceDetailView(LoginRequiredMixin, AdministratorRequiredMixin, DetailView):
    model = LearningResource
    context_object_name = 'resource'

    def get_object(self, queryset=None):
        try:
            course_id = self.kwargs.get('course_id')
            resource_id = self.kwargs.get('pk')
            
            obj = get_object_or_404(LearningResource, pk=resource_id, course__id=course_id)
            
            return obj
        except LearningResource.DoesNotExist:
            logger.error(f"LearningResource with id {resource_id} not found in course {course_id}")
            raise Http404("Learning Resource does not exist in the specified course")
        except Course.DoesNotExist:
            logger.error(f"Course with id {course_id} not found")
            raise Http404("Course does not exist")
        except PermissionDenied as e:
            logger.warning(f"Permission denied for user {self.request.user.username}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in AdministratorLearningResourceDetailView get_object: {str(e)}")
            raise Http404("An unexpected error occurred")

    def get_template_names(self):
        resource_type = self.object.resource_type.lower()
        return [
            f'users/administrator/course/learning_resource/{resource_type}_detail.html',
            'users/administrator/course/learning_resource/base_detail.html'
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['course'] = self.object.course
            context['is_administrator'] = True

            # Add resource-specific context data
            if self.object.resource_type == 'SCORM':
                context['scorm_details'] = self.object.scorm_details
                context['SCORM_API_BASE_URL'] = settings.SCORM_API_BASE_URL
                context['SCORM_PLAYER_USER_ID'] = self.request.user.scorm_profile.scorm_player_id
                context['SCORM_PLAYER_API_TOKEN'] = self.request.user.scorm_profile.token
            elif self.object.resource_type == 'QUIZ':
                context['quiz_details'] = self.object.quiz
            # Add more resource-specific context as needed

            # Add general resource metadata
            context['resource_metadata'] = {
                'created_at': self.object.created_at,
                'updated_at': self.object.updated_at,
                'is_mandatory': self.object.is_mandatory,
                'order': self.object.order,
            }

        except Exception as e:
            logger.error(f"Error in AdministratorLearningResourceDetailView get_context_data: {str(e)}")
        return context

# ============================================================
# ============================ Quiz Views ====================
# ============================================================    

class QuizCreateView(LoginRequiredMixin, AdministratorRequiredMixin, CreateView):
    model = Quiz
    form_class = QuizForm
    template_name = 'users/administrator/course/learning_resource/quizzes/quiz_create.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.permission_classes[0]().has_permission(request, self):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, pk=self.kwargs['course_id'])
        context['learning_resource'] = get_object_or_404(LearningResource, pk=self.kwargs['resource_id'])
        return context

    def form_valid(self, form):
        learning_resource = get_object_or_404(LearningResource, pk=self.kwargs['resource_id'])
        form.instance.learning_resource = learning_resource
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('administrator_quiz_add_questions', kwargs={
            'course_id': self.kwargs['course_id'],
            'resource_id': self.kwargs['resource_id'],
            'quiz_id': self.object.id
        })

class QuizAddQuestionsView(LoginRequiredMixin, AdministratorRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = 'users/administrator/course/learning_resource/quizzes/quiz_add_questions.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.permission_classes[0]().has_permission(request, self):
            return self.handle_no_permission()
        self.quiz = get_object_or_404(Quiz, pk=self.kwargs['quiz_id'])
        self.course = get_object_or_404(Course, pk=self.kwargs['course_id'])
        self.learning_resource = get_object_or_404(LearningResource, pk=self.kwargs['resource_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quiz'] = self.quiz
        context['course'] = self.course
        context['learning_resource'] = self.learning_resource
        ChoiceFormSet = formset_factory(ChoiceForm, extra=4)
        context['choice_formset'] = ChoiceFormSet(prefix='choices')
        return context

    def form_valid(self, form):
        question = form.save(commit=False)
        question.quiz = self.quiz
        question.save()

        question_type = form.cleaned_data['question_type']

        if question_type in ['MULTIPLE_CHOICE', 'TRUE_FALSE']:
            ChoiceFormSet = formset_factory(ChoiceForm, extra=4)
            choice_formset = ChoiceFormSet(self.request.POST, prefix='choices')
            
            if choice_formset.is_valid():
                logging.info("Choice formset is valid")
                for index, choice_form in enumerate(choice_formset):
                    if choice_form.cleaned_data:
                        choice = choice_form.save(commit=False)
                        choice.question = question
                        if question_type == 'TRUE_FALSE':
                            # For True/False, set 'True' as correct and 'False' as incorrect
                            choice.is_correct = (index == 0)  # First choice is 'True'
                        choice.save()
                        logging.info(f"Choice {choice.text} saved for question {question.id}")
            else:
                logging.error("Choice formset is not valid")
                logging.error(choice_formset.errors)
                # Handle the case when the formset is not valid
                return self.form_invalid(form)
        elif question_type == 'SHORT_ANSWER':
            short_answer_key = form.cleaned_data.get('short_answer_key')
            Choice.objects.create(
                question=question,
                text=short_answer_key,
                is_correct=True
            )
        elif question_type == 'ESSAY':
            essay_rubric = form.cleaned_data.get('essay_rubric')
            Choice.objects.create(
                question=question,
                text=essay_rubric,
                is_correct=True  
            )

        return redirect('administrator_quiz_add_questions', course_id=self.course.id, resource_id=self.learning_resource.id, quiz_id=self.quiz.id)

    def form_invalid(self, form):
        logging.error("Form is invalid")
        logging.error(form.errors)
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('administrator_quiz_add_questions', kwargs={
            'course_id': self.course.id,
            'resource_id': self.learning_resource.id,
            'quiz_id': self.quiz.id
        })

class QuizEditView(LoginRequiredMixin, AdministratorRequiredMixin, UpdateView):
    model = Quiz
    form_class = QuizForm
    template_name = 'users/administrator/course/learning_resource/quizzes/quiz_edit.html'

    def dispatch(self, request, *args, **kwargs):
        if not all(permission().has_permission(request, self) for permission in self.permission_classes):
            return self.handle_no_permission()
        self.course = get_object_or_404(Course, pk=self.kwargs['course_id'])
        self.learning_resource = get_object_or_404(LearningResource, pk=self.kwargs['resource_id'], course=self.course)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.learning_resource.quiz

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['question_formset'] = QuestionFormSet(self.request.POST, instance=self.object)
            context['choice_formsets'] = [
                ChoiceFormSet(self.request.POST, instance=question, prefix=f'choices_{question.id}')
                for question in self.object.questions.all()
            ]
        else:
            context['question_formset'] = QuestionFormSet(instance=self.object)
            context['choice_formsets'] = [
                ChoiceFormSet(instance=question, prefix=f'choices_{question.id}')
                for question in self.object.questions.all()
            ]
        context['course'] = self.course
        context['learning_resource'] = self.learning_resource
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        question_formset = context['question_formset']
        choice_formsets = context['choice_formsets']

        with transaction.atomic():
            self.object = form.save()
            if question_formset.is_valid():
                questions = question_formset.save(commit=False)
                for question in questions:
                    question.quiz = self.object
                    question.save()
                for question in question_formset.deleted_objects:
                    question.delete()
                
                for index, question in enumerate(self.object.questions.all()):
                    choice_formset = ChoiceFormSet(self.request.POST, instance=question, prefix=f'choices_{question.id}')
                    if choice_formset.is_valid():
                        choices = choice_formset.save(commit=False)
                        for choice in choices:
                            choice.question = question
                            choice.save()
                        for choice in choice_formset.deleted_objects:
                            choice.delete()
                    else:
                        return self.form_invalid(form)

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('administrator_learning_resource_detail', kwargs={
            'course_id': self.course.id,
            'pk': self.learning_resource.id
        })

# ============================================================
# ======================= Course Delivery Views ==============
# ============================================================

class AdministratorDeliveryCreateView(LoginRequiredMixin, AdministratorRequiredMixin, CreateView):
    model = Delivery
    form_class = DeliveryCreateForm
    template_name = 'users/administrator/course/deliveries/delivery_create.html'
    success_url = reverse_lazy('administrator_delivery_list')  

    def form_valid(self, form):
        try:
            delivery = form.save(commit=False)
            if delivery.delivery_type == 'PROGRAM':
                delivery.course = None
            else:
                delivery.program = None
            delivery.save()
            logger.info(f"Delivery '{delivery.title}' created successfully by {self.request.user}")
            messages.success(self.request, f"Delivery '{delivery.title}' has been created successfully.")
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error creating delivery: {str(e)}")
            messages.error(self.request, "An error occurred while creating the delivery. Please try again.")
            return self.form_invalid(form)

    def form_invalid(self, form):
        logger.warning(f"Invalid form submission: {form.errors}")
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)

    def handle_no_permission(self):
        logger.warning(f"Unauthorized access attempt to create delivery by user {self.request.user}")
        messages.error(self.request, "You do not have permission to create deliveries.")
        return super().handle_no_permission()

class AdministratorDeliveryListView(LoginRequiredMixin, AdministratorRequiredMixin, FilterView):
    model = Delivery
    template_name = 'users/administrator/course/deliveries/delivery_list.html'
    context_object_name = 'deliveries'
    filterset_class = DeliveryFilter
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-created_at')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'deliveries'
        
        try:
            context['total_deliveries'] = Delivery.objects.count()
            context['active_deliveries'] = Delivery.objects.filter(is_active=True).count()
            context['program_deliveries'] = Delivery.objects.filter(delivery_type='PROGRAM').count()
            context['course_deliveries'] = Delivery.objects.filter(delivery_type='COURSE').count()
        except Exception as e:
            logger.error(f"Error fetching delivery statistics: {str(e)}")
            context['stats_error'] = "Unable to fetch delivery statistics."

        return context
    
class AdministratorDeliveryDetailView(LoginRequiredMixin, AdministratorRequiredMixin, DetailView):
    model = Delivery
    template_name = 'users/administrator/course/deliveries/delivery_detail.html'
    context_object_name = 'delivery'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        delivery = self.object

        # Get all components for this delivery
        components = DeliveryComponent.objects.filter(delivery=delivery)

        # Count metrics
        component_counts = components.aggregate(
            total=Count('id'),
            mandatory_count=Count('id', filter=Q(is_mandatory=True)),
            optional_count=Count('id', filter=Q(is_mandatory=False))
        )

        # Enrollment count
        enrollment_count = Enrollment.objects.filter(delivery=delivery).count()

        context['components'] = {
            'count': component_counts['total'],
            'mandatory_count': component_counts['mandatory_count'],
            'optional_count': component_counts['optional_count'],
        }
        context['enrollment_stats'] = {
            'total': enrollment_count,
        }

        if delivery.delivery_type == 'PROGRAM':
            context['program_courses'] = components.filter(
                program_course__isnull=False,
                parent_component__isnull=True
            ).select_related('program_course__course').order_by('order')
        else:
            context['learning_resources'] = components.filter(
                learning_resource__isnull=False
            ).select_related('learning_resource').order_by('order')

        return context
    
class AdministratorDeliveryEditView(LoginRequiredMixin, AdministratorRequiredMixin, UpdateView):
    model = Delivery
    form_class = DeliveryEditForm
    template_name = 'users/administrator/course/deliveries/delivery_edit.html'
    context_object_name = 'delivery'

    def get_success_url(self):
        return reverse_lazy('administrator_delivery_detail', kwargs={'pk': self.object.pk})
    
class AdministratorDeliveryDeleteView(LoginRequiredMixin, AdministratorRequiredMixin, DeleteView):
    model = Delivery
    success_url = reverse_lazy('administrator_delivery_list')
    
    def delete(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            self.object.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': _('Error deleting delivery: {}').format(str(e))}, status=400)

    def handle_no_permission(self):
        return JsonResponse({'error': _('You do not have permission to delete this delivery.')}, status=403)

class CourseComponentCreateView(LoginRequiredMixin, AdministratorRequiredMixin, CreateView):
    model = DeliveryComponent
    form_class = CourseComponentForm
    template_name = 'users/administrator/course/deliveries/course_component_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['delivery'] = get_object_or_404(Delivery, pk=self.kwargs['delivery_id'])
        return kwargs

    def form_valid(self, form):
        form.instance.delivery = form.delivery
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('administrator_delivery_detail', kwargs={'pk': self.kwargs['delivery_id']})

class ResourceComponentCreateView(LoginRequiredMixin, AdministratorRequiredMixin, CreateView):
    model = DeliveryComponent
    form_class = ResourceComponentForm
    template_name = 'users/administrator/course/deliveries/resource_component_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if 'delivery_id' in self.kwargs:
            kwargs['delivery'] = get_object_or_404(Delivery, pk=self.kwargs['delivery_id'])
        elif 'parent_component_id' in self.kwargs:
            kwargs['parent_component'] = get_object_or_404(DeliveryComponent, pk=self.kwargs['parent_component_id'])
        return kwargs

    def form_valid(self, form):
        if 'delivery_id' in self.kwargs:
            form.instance.delivery = get_object_or_404(Delivery, pk=self.kwargs['delivery_id'])
        elif 'parent_component_id' in self.kwargs:
            parent_component = get_object_or_404(DeliveryComponent, pk=self.kwargs['parent_component_id'])
            form.instance.delivery = parent_component.delivery
            form.instance.parent_component = parent_component
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('administrator_delivery_detail', kwargs={'pk': self.object.delivery.pk})


class AdministratorDeliveryComponentEditView(LoginRequiredMixin, AdministratorRequiredMixin, UpdateView):
    template_name = 'users/administrator/course/deliveries/delivery_component_edit.html'
 

class AdministratorDeliveryComponentDeleteView(LoginRequiredMixin, AdministratorRequiredMixin, DeleteView):
    model = DeliveryComponent
    template_name = 'users/administrator/course/deliveries/delivery_component_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('administrator_delivery_detail', kwargs={'pk': self.object.delivery.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Delivery component deleted successfully.')
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['delivery'] = self.object.delivery
        return context

class DeliveryEnrollmentListView(LoginRequiredMixin, ListView):
    model = Enrollment
    template_name = 'users/administrator/course/deliveries/enrollments/enrollment_list.html'
    context_object_name = 'enrollments'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        try:
            self.delivery = get_object_or_404(Delivery, id=self.kwargs['delivery_id'])
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in DeliveryEnrollmentListView dispatch: {str(e)}")
            messages.error(self.request, _("An error occurred while accessing the delivery enrollments."))
            return self.handle_no_permission()

    def get_queryset(self):
        try:
            queryset = Enrollment.objects.filter(delivery=self.delivery).select_related('user', 'delivery')
            self.filterset = EnrollmentFilter(self.request.GET, queryset=queryset)
            return self.filterset.qs
        except Exception as e:
            logger.error(f"Error in DeliveryEnrollmentListView get_queryset: {str(e)}")
            messages.error(self.request, _("An error occurred while fetching enrollments."))
            return Enrollment.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['delivery'] = self.delivery
            context['filterset'] = self.filterset

            # Enrollment statistics
            context['total_enrollments'] = self.filterset.qs.count()
            context['active_enrollments'] = self.filterset.qs.filter(status__in=['ENROLLED', 'IN_PROGRESS']).count()
            context['completed_enrollments'] = self.filterset.qs.filter(status='COMPLETED').count()

        except Exception as e:
            logger.error(f"Error in DeliveryEnrollmentListView get_context_data: {str(e)}")
            messages.error(self.request, _("An error occurred while preparing the enrollment data."))

        return context

class DeliveryEnrollmentsCreateView(LoginRequiredMixin, FormView):
    template_name = 'users/administrator/course/deliveries/enrollments/enrollment_create.html'
    form_class = EnrollmentForm

    def dispatch(self, request, *args, **kwargs):
        self.delivery = get_object_or_404(Delivery, pk=self.kwargs['delivery_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user_filter = UserFilter(self.request.GET, queryset=User.objects.all())
        kwargs['delivery'] = self.delivery
        kwargs['user_queryset'] = user_filter.qs
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['delivery'] = self.delivery
        user_filter = UserFilter(self.request.GET, queryset=User.objects.all())
        context['filter'] = user_filter
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                selected_users = form.cleaned_data['selected_users']
                for user in selected_users:
                    enrollment, created = Enrollment.objects.get_or_create(
                        user=user,
                        delivery=self.delivery,
                        defaults={'status': 'ENROLLED'}
                    )
                    if created:
                        logger.info(f"User {user.username} enrolled in delivery {self.delivery.title}")
                    else:
                        logger.info(f"User {user.username} already enrolled in delivery {self.delivery.title}")

                messages.success(self.request, f"{len(selected_users)} users have been enrolled in {self.delivery.title}")
        except Exception as e:
            logger.error(f"Error during enrollment process: {str(e)}")
            messages.error(self.request, "An error occurred during the enrollment process. Please try again.")
            return self.form_invalid(form)

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('administrator_delivery_enrollments', kwargs={'delivery_id': self.delivery.id})
# ============================================================
# ======================= Program Views ======================
# ============================================================

class AdministratorProgramListView(LoginRequiredMixin, AdministratorRequiredMixin, ListView):
    model = Program
    template_name = 'users/administrator/program/program_list.html'
    context_object_name = 'programs'
    paginate_by = 10

    def get_queryset(self):
        return Program.objects.all().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_programs'] = Program.objects.count()
        context['published_programs'] = Program.objects.filter(is_published=True).count()
        context['unpublished_programs'] = Program.objects.filter(is_published=False).count()
        context['top_tags'] = Tag.objects.annotate(
            program_count=Count('program')
        ).order_by('-program_count')[:5]
        context['all_tags'] = Tag.objects.all()
        return context
    

class AdministratorProgramDetailView(LoginRequiredMixin, AdministratorRequiredMixin, DetailView):
    model = Program
    template_name = 'users/administrator/program/program_detail.html'
    context_object_name = 'program'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['program_courses'] = ProgramCourse.objects.filter(program=self.object).order_by('order')
        return context
    

class AdministratorProgramCreateView(LoginRequiredMixin, AdministratorRequiredMixin, CreateView):
    model = Program
    form_class = ProgramForm
    template_name = 'users/administrator/program/program_create.html'
    success_url = reverse_lazy('administrator_program_list')  

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class AdministratorProgramDeleteView(LoginRequiredMixin, AdministratorRequiredMixin, DeleteView):
    model = Program
    template_name = 'users/administrator/program/program_confirm_delete.html'
    success_url = reverse_lazy('administrator_program_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "The program was successfully deleted.")
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['program'] = self.get_object()
        return context
    
class AdministratorProgramEditView(LoginRequiredMixin, AdministratorRequiredMixin, UpdateView):
    model = Program
    form_class = ProgramForm
    template_name = 'users/administrator/program/program_edit.html'

    def get_success_url(self):
        return reverse_lazy('administrator_program_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "The program was successfully updated.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There was an error updating the program. Please check the form and try again.")
        return super().form_invalid(form)
    

class AdministratorProgramPublishView(LoginRequiredMixin, AdministratorRequiredMixin, FormView):
    template_name = 'users/administrator/program/program_publish_confirm.html'
    form_class = ProgramPublishForm
    success_url = reverse_lazy('administrator_program_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['program'] = get_object_or_404(Program, pk=self.kwargs['pk'])
        return kwargs

    def form_valid(self, form):
        program = form.save()
        messages.success(self.request, f'Program "{program.title}" has been published.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['program'] = get_object_or_404(Program, pk=self.kwargs['pk'])
        return context

class AdministratorProgramUnpublishView(LoginRequiredMixin, AdministratorRequiredMixin, FormView):
    template_name = 'users/administrator/program/program_unpublish_confirm.html'
    form_class = ProgramUnpublishForm
    success_url = reverse_lazy('administrator_program_list')  

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['program'] = get_object_or_404(Program, pk=self.kwargs['pk'])
        return kwargs

    def form_valid(self, form):
        program = form.save()
        messages.success(self.request, f'Program "{program.title}" has been unpublished.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['program'] = get_object_or_404(Program, pk=self.kwargs['pk'])
        return context
    

class AdministratorProgramCourseCreateView(LoginRequiredMixin, AdministratorRequiredMixin, CreateView):
    model = ProgramCourse
    form_class = ProgramCourseForm
    template_name = 'users/administrator/program/program_course_create.html'

    def get_success_url(self):
        return reverse_lazy('administrator_program_detail', kwargs={'pk': self.kwargs['program_id']})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['program'] = get_object_or_404(Program, pk=self.kwargs['program_id'])
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['program'] = get_object_or_404(Program, pk=self.kwargs['program_id'])
        return context
    
# ============================================================
# ======================= Enrollments Views ==================
# ============================================================

class AdministratorEnrollmentCreateView(LoginRequiredMixin, AdministratorRequiredMixin, FormView):
    template_name = 'users/administrator/enrollments/enrollment_create.html'
    form_class = EnrollmentForm
    success_url = reverse_lazy('administrator_enrollment_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all()
        return context

    def form_valid(self, form):
        enrollment_type = form.cleaned_data['enrollment_type']
        delivery = form.cleaned_data.get('delivery')
        program = form.cleaned_data.get('program')
        course = form.cleaned_data.get('course')
        
        selected_users = self.request.POST.getlist('selected_users')
        users = User.objects.filter(id__in=selected_users)

        enrollments_created = 0
        already_enrolled = []
        errors = []

        for user in users:
            enrollment_data = {
                'user': user,
                'status': 'ENROLLED'
            }

            if enrollment_type == 'delivery':
                enrollment_data['delivery'] = delivery
                existing_enrollment = Enrollment.objects.filter(user=user, delivery=delivery).exists()
            elif enrollment_type == 'program':
                enrollment_data['program'] = program
                existing_enrollment = Enrollment.objects.filter(user=user, program=program).exists()
            else:
                enrollment_data['course'] = course
                existing_enrollment = Enrollment.objects.filter(user=user, course=course).exists()

            if existing_enrollment:
                already_enrolled.append(user.username)
                continue

            try:
                Enrollment.objects.create(**enrollment_data)
                enrollments_created += 1
            except IntegrityError:
                already_enrolled.append(user.username)
            except Exception as e:
                errors.append(f"Error enrolling {user.username}: {str(e)}")

        if enrollments_created > 0:
            messages.success(self.request, _(f"{enrollments_created} enrollments created successfully."))
        
        if already_enrolled:
            messages.warning(self.request, _(f"The following users were already enrolled: {', '.join(already_enrolled)}"))
        
        if errors:
            for error in errors:
                messages.error(self.request, _(error))
        
        if errors or not enrollments_created:
            return self.form_invalid(form)
        
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{form.fields[field].label}: {error}")
        return super().form_invalid(form)
    
class AdministratorEnrollmentEditView(LoginRequiredMixin, AdministratorRequiredMixin, UpdateView):
    model = Enrollment
    form_class = EnrollmentEditForm
    template_name = 'users/administrator/enrollments/enrollment_edit.html'
    success_url = reverse_lazy('administrator_enrollment_list')

    def get_object(self, queryset=None):
        return get_object_or_404(Enrollment, pk=self.kwargs['pk'])

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Enrollment updated successfully."))
        return response

class AdministratorEnrollmentDeleteView(DeleteView):
    model = Enrollment
    template_name = 'users/administrator/enrollments/enrollment_confirm_delete.html'
    success_url = reverse_lazy('administrator_enrollment_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _("Enrollment deleted successfully."))
        return super().delete(request, *args, **kwargs)

# ============================================================
# =============== Organization Hierarcy Views ================
# ============================================================

class OrganizationDetailsView(LoginRequiredMixin, AdministratorRequiredMixin, TemplateView):
    template_name = 'users/administrator/organization/organization_details.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            organization = Organization.objects.first()
            if not organization:
                logger.error("No organization found in the system")
                raise Http404("No organization found in the system")

            context['organization'] = organization
            context['organization_units'] = OrganizationUnit.objects.filter(organization=organization).select_related('parent', 'manager')
            context['locations'] = Location.objects.filter(organization=organization)
            context['contacts'] = OrganizationContact.objects.filter(organization=organization)

            logger.info(f"Organization details retrieved successfully for {organization.name}")
        except ObjectDoesNotExist as e:
            logger.error(f"Error retrieving organization details: {str(e)}")
            raise Http404("Organization not found")
        except Exception as e:
            logger.error(f"Unexpected error in OrganizationDetailsView: {str(e)}")
            raise

        return context

class OrganizationUnitsView(LoginRequiredMixin, AdministratorRequiredMixin, ListView):
    template_name = 'users/administrator/organization/organization_units.html'
    model = OrganizationUnit
    context_object_name = 'organization_units'
    paginate_by = 10
    permission_required = 'organization.view_organizationunit'

    def get_queryset(self):
        try:
            organization = Organization.objects.first()
            queryset = OrganizationUnit.objects.filter(organization=organization)
            self.filterset = OrganizationUnitFilter(self.request.GET, queryset=queryset)
            return self.filterset.qs
        except Exception as e:
            logger.error(f"Error in OrganizationUnitsView get_queryset: {str(e)}")
            messages.error(self.request, _("An error occurred while fetching organization units. Please try again later."))
            return OrganizationUnit.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['filterset'] = self.filterset
        except Exception as e:
            logger.error(f"Error in OrganizationUnitsView get_context_data: {str(e)}")
            messages.error(self.request, _("An error occurred while preparing the page. Please try again later."))
        return context
    
class OrganizationLocationsView(LoginRequiredMixin, AdministratorRequiredMixin, ListView):
    template_name = 'users/administrator/organization/organization_locations.html'
    model = Location
    context_object_name = 'locations'
    paginate_by = 10
    permission_required = 'organization.view_location'

    def get_queryset(self):
        try:
            organization = Organization.objects.first()
            queryset = Location.objects.filter(organization=organization)
            self.filterset = LocationFilter(self.request.GET, queryset=queryset)
            return self.filterset.qs
        except Exception as e:
            logger.error(f"Error in OrganizationLocationsView get_queryset: {str(e)}")
            messages.error(self.request, _("An error occurred while fetching locations. Please try again later."))
            return Location.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['filterset'] = self.filterset
        except Exception as e:
            logger.error(f"Error in OrganizationLocationsView get_context_data: {str(e)}")
            messages.error(self.request, _("An error occurred while preparing the page. Please try again later."))
        return context
    
class OrganizationJobPositionsView(LoginRequiredMixin, AdministratorRequiredMixin, ListView):
    template_name = 'users/administrator/organization/organization_job_positions.html'
    model = JobPosition
    context_object_name = 'job_positions'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = JobPositionFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        return context
    
class OrganizationEmployeeProfilesView(LoginRequiredMixin, AdministratorRequiredMixin, ListView):
    template_name = 'users/administrator/organization/organization_employee_profiles.html'
    model = EmployeeProfile
    context_object_name = 'employee_profiles'
    paginate_by = 10  

    def get_queryset(self):
        try:
            organization = Organization.objects.first()
            queryset = EmployeeProfile.objects.filter(organization=organization)
            self.filterset = EmployeeProfileFilter(self.request.GET, queryset=queryset)
            return self.filterset.qs
        except Exception as e:
            logger.error(f"Error in OrganizationEmployeeProfilesView get_queryset: {str(e)}")
            messages.error(self.request, _("An error occurred while fetching employee profiles. Please try again later."))
            return EmployeeProfile.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['filterset'] = self.filterset
        except Exception as e:
            logger.error(f"Error in OrganizationEmployeeProfilesView get_context_data: {str(e)}")
            messages.error(self.request, _("An error occurred while preparing the page. Please try again later."))
        return context
    
class OrganizationGroupsView(LoginRequiredMixin, AdministratorRequiredMixin, ListView):
    template_name = 'users/administrator/organization/organization_groups.html'
    model = Group
    context_object_name = 'groups'
    paginate_by = 10
    permission_required = 'auth.view_group'

    def get_queryset(self):
        try:
            queryset = Group.objects.all()
            self.filterset = GroupFilter(self.request.GET, queryset=queryset)
            return self.filterset.qs
        except Exception as e:
            logger.error(f"Error in OrganizationGroupsView get_queryset: {str(e)}")
            messages.error(self.request, _("An error occurred while fetching groups. Please try again later."))
            return Group.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['filterset'] = self.filterset
        except Exception as e:
            logger.error(f"Error in OrganizationGroupsView get_context_data: {str(e)}")
            messages.error(self.request, _("An error occurred while preparing the page. Please try again later."))
        return context
    
# ============================================================
# =============== Organization Employee Views ================
# ============================================================

class AddEmployeeView(LoginRequiredMixin, AdministratorRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = 'users/administrator/organization/employee/add_employee.html'
    form_class = EmployeeProfileForm
    success_url = reverse_lazy('administrator_organization_employee_profiles')
    success_message = "Employee profile created successfully."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = Organization.objects.first()  
        kwargs['request'] = self.request
        return kwargs
    
# ============================================================
# ============ Organization JobPositions Views ===============
# ============================================================

class AddJobPositionView(LoginRequiredMixin, AdministratorRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = 'users/administrator/organization/job_position/add_job_position.html'
    form_class = JobPositionForm
    success_url = reverse_lazy('administrator_organization_job_positions')
    success_message = "Job position created successfully."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = Organization.objects.first()
        kwargs['request'] = self.request
        return kwargs
    
# ============================================================
# ============== Organization Location Views =================
# ============================================================

class AddLocationView(LoginRequiredMixin, AdministratorRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = 'users/administrator/organization/location/add_location.html'
    form_class = LocationForm
    success_url = reverse_lazy('administrator_organization_locations')
    success_message = "Location created successfully."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = Organization.objects.first()
        kwargs['request'] = self.request
        return kwargs

# ============================================================
# ============== Organization Unit Views =====================
# ============================================================

class AddOrganizationUnitView(LoginRequiredMixin, AdministratorRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = 'users/administrator/organization/unit/add_unit.html'
    form_class = OrganizationUnitForm
    success_url = reverse_lazy('administrator_organization_units')
    success_message = _("Organization unit created successfully.")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            logger.info(f"Organization unit created successfully: {self.object}")
            return response
        except Exception as e:
            logger.error(f"Error creating organization unit: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        logger.warning(f"Invalid form submission: {form.errors}")
        return super().form_invalid(form)

# ============================================================
# ============== Organization Group Views ====================
# ============================================================
    
class AddOrganizationGroupView(LoginRequiredMixin, AdministratorRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = 'users/administrator/organization/group/add_group.html'
    form_class = OrganizationGroupForm
    success_url = reverse_lazy('administrator_organization_groups')
    success_message = "Organization group created successfully."

# ============================================================
# ======================= Notifications Views ================
# ============================================================

class RecentNotificationsView(LoginRequiredMixin, AdministratorRequiredMixin, View):
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

class NotificationListView(LoginRequiredMixin, AdministratorRequiredMixin, FilterView, ListView):
    model = SystemNotification
    template_name = 'users/administrator/notifications/notifications_list.html'
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
        
class MarkNotificationReadView(LoginRequiredMixin, AdministratorRequiredMixin, View):
    def post(self, request, pk):
        try:
            notification = SystemNotification.objects.get(id=pk, user=request.user)
            notification.is_read = True
            notification.save()
            return redirect('administrator_notification_list')
        except SystemNotification.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return JsonResponse({'status': 'error', 'message': 'An error occurred'}, status=500)

class MarkAllNotificationsReadView(LoginRequiredMixin, AdministratorRequiredMixin, View):
    def post(self, request):
        SystemNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    
class UnreadNotificationsCountView(LoginRequiredMixin, AdministratorRequiredMixin, View):
    def get(self, request):
        try:
            count = SystemNotification.objects.filter(user=request.user, is_read=False).count()
            return JsonResponse({'count': count})
        except Exception as e:
            logger.error(f"Error fetching unread notifications count for user {request.user}: {e}")
            return JsonResponse({'count': 0})