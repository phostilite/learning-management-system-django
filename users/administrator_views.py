import logging
import json
from datetime import timedelta

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import TemplateView, DetailView, ListView, FormView, DeleteView, UpdateView
from django.views.generic.edit import CreateView
from formtools.wizard.views import SessionWizardView
from rest_framework import status
from rest_framework.permissions import BasePermission, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions
from django.core.exceptions import PermissionDenied


from certificates.models import Certificate
from courses.forms import (CourseForm, EnrollmentForm, LearningResourceForm,
                           LearningResourceFormSet, ScormResourceForm, ProgramForm, ProgramPublishForm, ProgramUnpublishForm, LearningResourceEditForm, CoursePublishForm, CourseUnpublishForm, ProgramCourseForm, DeliveryCreateForm, DeliveryEditForm, EnrollmentEditForm, CourseComponentForm, ResourceComponentForm)
from courses.models import (Course, CourseCategory, Enrollment, LearningResource, ScormResource, Tag, Program, ProgramCourse, Delivery, DeliveryComponent)
from users.forms import LearnerCreationForm
from users.models import Learner, Facilitator, Supervisor, SCORMUserProfile
from .api_client import create_scormhub_course, register_user_for_course, upload_scorm_package

# Initialize logger
logger = logging.getLogger(__name__)

# Get the user model
User = get_user_model()
class IsInAdministratorGroup(permissions.BasePermission):
    message = "User does not have administrator privileges."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            logger.warning(f"Unauthenticated user attempted to access {view.__class__.__name__}")
            return False

        try:
            is_admin = request.user.groups.filter(name='administrator').exists()
            if not is_admin:
                logger.warning(f"User {request.user.username} attempted to access {view.__class__.__name__} without administrator privileges")
            return is_admin
        except ObjectDoesNotExist:
            logger.error(f"Error checking administrator group for user {request.user.username}")
            return False

    def has_object_permission(self, request, view, obj):
        # If the user has general permission, we also grant object-level permission
        return self.has_permission(request, view)

@method_decorator(login_required, name='dispatch')
class AdministratorDashboardView(TemplateView):
    template_name = 'users/administrator/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class AdministratorCalendarView(TemplateView):
    template_name = 'users/administrator/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class AdministratorLeaderboardView(TemplateView):
    template_name = 'users/administrator/leaderboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class AdministratorCertificateListView(ListView):
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
    
class AdministratorAnnouncementListView(TemplateView):
    template_name = 'users/administrator/announcements.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class AdministratorHelpSupportView(TemplateView):
    template_name = 'users/administrator/help_support.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class AdministratorMessageListView(TemplateView):
    template_name = 'users/administrator/messages.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class AdministratorSettingsView(TemplateView):
    template_name = 'users/administrator/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    
class AdministratorLearningPathListView(TemplateView):
    template_name = 'users/administrator/course/learning_path.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class AdministratorCourseCompletionReportView(TemplateView):
    template_name = 'users/administrator/reports/course_completion.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class AdministratorUserProgressReportView(TemplateView):
    template_name = 'users/administrator/reports/user_progress.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class AdministratorAssessmentResultsReportView(TemplateView):
    template_name = 'users/administrator/reports/assessment_results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class AdministratorUserEngagementReportView(TemplateView):
    template_name = 'users/administrator/reports/user_engagement.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class AdministratorResourceUsageReportView(TemplateView):
    template_name = 'users/administrator/reports/resource_usage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class AdministratorCertificationTrackingReportView(TemplateView):
    template_name = 'users/administrator/reports/certification_tracking.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class AdministratorLearnerFeedbackReportView(TemplateView):
    template_name = 'users/administrator/reports/learner_feedback.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class AdministratorCustomReportView(TemplateView):
    template_name = 'users/administrator/reports/custom_reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
@method_decorator(login_required, name='dispatch')
class AdministratorLearnerListView(ListView):
    template_name = 'users/administrator/learners.html'
    context_object_name = 'learners'

    def get_queryset(self):
        return Learner.objects.all()
    
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
                
                # Create Learner (without token)
                Learner.objects.create(user=user)
                logger.info(f"Learner created for user: {user.username}")
                
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



@method_decorator(login_required, name='dispatch')
class AdministratorFacilitatorListView(ListView):
    template_name = 'users/administrator/facilitators.html'
    context_object_name = 'facilitators'

    def get_queryset(self):
        return Facilitator.objects.all()
    
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

            facilitator = Facilitator.objects.create(user=user)
            logger.info(f"Facilitator created: {facilitator.id}")

            return redirect('administrator_facilitator_list')  # Redirect to the list view after creation

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
    

@method_decorator(login_required, name='dispatch')
class AdministratorSupervisorListView(ListView):
    template_name = 'users/administrator/supervisors.html'
    context_object_name = 'supervisors'

    def get_queryset(self):
        return Supervisor.objects.all()
    
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

            supervisor = Supervisor.objects.create(user=user)
            logger.info(f"Supervisor created: {supervisor.id}")

            return redirect('administrator_supervisor_list')  # Redirect to the list view after creation

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

@method_decorator(login_required, name='dispatch')
class AdministratorCourseCategoryListView(ListView):
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

class AdministratorCourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'users/administrator/course/course_create.html'
    success_url = reverse_lazy('administrator_course_list')

    def test_func(self):
        return self.request.user.groups.filter(name='administrator').exists()

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class AdministratorCourseListView(ListView):
    template_name = 'users/administrator/course/course_list.html'
    context_object_name = 'courses'

    def get_queryset(self):
        try:
            courses = Course.objects.filter(created_by=self.request.user).select_related('category')
            logger.info(f"Fetched {len(courses)} courses for user {self.request.user.id}")
            return courses
        except Exception as e:
            logger.exception("Error fetching course list:")
            messages.error(self.request, f"An error occurred while fetching the course list: {str(e)}")
            return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Fetch course metrics efficiently
        course_metrics = Course.objects.filter(created_by=self.request.user).aggregate(
            total_courses=Count('id'),
            published_courses=Count('id', filter=Q(is_published=True)),
            unpublished_courses=Count('id', filter=Q(is_published=False))
        )
        
        # Fetch category metrics
        category_metrics = CourseCategory.objects.filter(
            course__created_by=self.request.user
        ).annotate(course_count=Count('course')).order_by('-course_count')[:5]

        all_categories = CourseCategory.objects.all().order_by('name')

        context.update({
            'total_courses': course_metrics['total_courses'],
            'published_courses': course_metrics['published_courses'],
            'unpublished_courses': course_metrics['unpublished_courses'],
            'top_categories': category_metrics,
            'all_categories': all_categories,
        })
        
        return context


class AdministratorCourseDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Course
    template_name = 'users/administrator/course/course_detail.html'
    context_object_name = 'course'

    def test_func(self):
        return self.request.user.groups.filter(name='administrator').exists()

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


class AdministratorCourseEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'users/administrator/course/course_edit.html'

    def test_func(self):
        return self.request.user.groups.filter(name='administrator').exists()

    def get_success_url(self):
        return reverse_lazy('administrator_course_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.object
        context['tags'] = Tag.objects.all()
        return context
    
    
class AdministratorCoursePublishView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'users/administrator/course/course_publish_confirm.html'
    form_class = CoursePublishForm
    success_url = reverse_lazy('administrator_course_list')

    def test_func(self):
        return self.request.user.groups.filter(name='administrator').exists()

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
    
class AdministratorCourseUnpublishView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'users/administrator/course/course_unpublish_confirm.html'
    form_class = CourseUnpublishForm
    success_url = reverse_lazy('administrator_course_list')

    def test_func(self):
        return self.request.user.groups.filter(name='administrator').exists()

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

    

class AdministratorCourseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Course
    template_name = 'users/administrator/course/course_delete_confirm.html'
    success_url = reverse_lazy('administrator_course_list')
    
    def test_func(self):
        return self.request.user.groups.filter(name='administrator').exists()

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, ("The course was successfully deleted."))
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = ("Delete Course")
        return context
    
# ============================================================
# =================== Course Enrollment Views ================
# ============================================================

class AdministratorEnrollmentListView(ListView):
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

class AdministratorLearningResourcesListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = LearningResource
    template_name = 'users/administrator/course/learning_resource/learning_resource_list.html'
    context_object_name = 'learning_resources'

    def test_func(self):
        return hasattr(self.request.user, 'administrator')

    def get_queryset(self):
        self.course = get_object_or_404(Course, id=self.kwargs['course_id'])
        return LearningResource.objects.filter(course=self.course)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.course
        return context
    
class AdministratorLearningResourceCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = LearningResource
    form_class = LearningResourceForm
    template_name = 'users/administrator/course/learning_resource/learning_resource_create.html'

    def test_func(self):
        return self.request.user.groups.filter(name='administrator').exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, pk=self.kwargs['course_id'])
        context['scorm_upload_url'] = reverse_lazy('scorm_upload')
        return context

    def form_valid(self, form):
        course = get_object_or_404(Course, pk=self.kwargs['course_id'])
        form.instance.course = course

        if form.instance.resource_type != 'SCORM':
            return super().form_valid(form)
        
        # For SCORM resources, we'll handle the creation in the template via AJAX
        return JsonResponse({'success': True, 'redirect_url': self.get_success_url()})

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
    

class AdministratorLearningResourceEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = LearningResource
    form_class = LearningResourceEditForm
    template_name = 'users/administrator/course/learning_resource/learning_resource_edit.html'
    pk_url_kwarg = 'resource_id'

    def test_func(self):
        return self.request.user.groups.filter(name='administrator').exists()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, id=self.kwargs['course_id'])
        return context

    def get_success_url(self):
        return reverse_lazy('administrator_course_detail', kwargs={'pk': self.kwargs['course_id']})
    

class AdministratorLearningResourceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = LearningResource
    template_name = 'users/administrator/course/learning_resource/learning_resource_delete_confirm.html'
    pk_url_kwarg = 'resource_id'
    context_object_name = 'learning_resource'

    def test_func(self):
        return self.request.user.groups.filter(name='administrator').exists()

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

class AdministratorLearningResourceDetailView(LoginRequiredMixin, DetailView):
    model = LearningResource
    context_object_name = 'resource'
    permission_classes = [IsInAdministratorGroup]

    def dispatch(self, request, *args, **kwargs):
        try:
            if not all(permission().has_permission(request, self) for permission in self.permission_classes):
                logger.warning(f"User {request.user.username} attempted to access AdministratorLearningResourceDetailView without proper permissions")
                raise PermissionDenied("You do not have administrator privileges.")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in AdministratorLearningResourceDetailView dispatch: {str(e)}")
            raise

    def get_object(self, queryset=None):
        try:
            course_id = self.kwargs.get('course_id')
            resource_id = self.kwargs.get('pk')
            
            obj = get_object_or_404(LearningResource, pk=resource_id, course__id=course_id)
            
            if not all(permission().has_object_permission(self.request, self, obj) for permission in self.permission_classes):
                logger.warning(f"User {self.request.user.username} attempted to access LearningResource {resource_id} without proper permissions")
                raise PermissionDenied("You do not have permission to view this resource.")
            
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
# ======================= Course Delivery Views ==============
# ============================================================

class AdministratorDeliveryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Delivery
    form_class = DeliveryCreateForm
    template_name = 'users/administrator/course/deliveries/delivery_create.html'
    success_url = reverse_lazy('administrator_delivery_list')  

    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'administrator')

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
    
class AdministratorDeliveryListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Delivery
    template_name = 'users/administrator/course/deliveries/delivery_list.html'
    context_object_name = 'deliveries'

    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'administrator')

    def get_queryset(self):
        return Delivery.objects.all().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'deliveries'  
        return context
    
class AdministratorDeliveryDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Delivery
    template_name = 'users/administrator/course/deliveries/delivery_detail.html'
    context_object_name = 'delivery'

    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'administrator')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        delivery = self.object
        if delivery.delivery_type == 'PROGRAM':
            context['program_courses'] = DeliveryComponent.objects.filter(
                delivery=delivery,
                program_course__isnull=False,
                parent_component__isnull=True
            ).select_related('program_course__course').order_by('order')
        else:
            context['learning_resources'] = DeliveryComponent.objects.filter(
                delivery=delivery,
                learning_resource__isnull=False
            ).select_related('learning_resource').order_by('order')
        return context
    
class AdministratorDeliveryEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Delivery
    form_class = DeliveryEditForm
    template_name = 'users/administrator/course/deliveries/delivery_edit.html'
    context_object_name = 'delivery'

    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'administrator')

    def get_success_url(self):
        return reverse_lazy('administrator_delivery_detail', kwargs={'pk': self.object.pk})
    
class AdministratorDeliveryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Delivery
    template_name = 'users/administrator/course/deliveries/delivery_confirm_delete.html'
    context_object_name = 'delivery'
    success_url = reverse_lazy('administrator_delivery_list')  

    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'administrator')

class CourseComponentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = DeliveryComponent
    form_class = CourseComponentForm
    template_name = 'users/administrator/course/deliveries/course_component_form.html'

    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'administrator')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['delivery'] = get_object_or_404(Delivery, pk=self.kwargs['delivery_id'])
        return kwargs

    def form_valid(self, form):
        form.instance.delivery = form.delivery
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('administrator_delivery_detail', kwargs={'pk': self.kwargs['delivery_id']})

class ResourceComponentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = DeliveryComponent
    form_class = ResourceComponentForm
    template_name = 'users/administrator/course/deliveries/resource_component_form.html'

    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'administrator')

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


class AdministratorDeliveryComponentEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = 'users/administrator/course/deliveries/delivery_component_edit.html'

class AdministratorDeliveryComponentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = DeliveryComponent
    template_name = 'users/administrator/course/deliveries/delivery_component_delete.html'
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'administrator')
    
    def get_success_url(self):
        return reverse_lazy('administrator_delivery_detail', kwargs={'pk': self.object.delivery.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Delivery component deleted successfully.')
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['delivery'] = self.object.delivery
        return context

# ============================================================
# ======================= Program Views ======================
# ============================================================

class AdministratorProgramListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Program
    template_name = 'users/administrator/program/program_list.html'
    context_object_name = 'programs'
    paginate_by = 10

    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'administrator')

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
    

class AdministratorProgramDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Program
    template_name = 'users/administrator/program/program_detail.html'
    context_object_name = 'program'

    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'administrator')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['program_courses'] = ProgramCourse.objects.filter(program=self.object).order_by('order')
        return context
    

class AdministratorProgramCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Program
    form_class = ProgramForm
    template_name = 'users/administrator/program/program_create.html'
    success_url = reverse_lazy('administrator_program_list')  

    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'administrator')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class AdministratorProgramDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Program
    template_name = 'users/administrator/program/program_confirm_delete.html'
    success_url = reverse_lazy('administrator_program_list')

    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'administrator')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "The program was successfully deleted.")
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['program'] = self.get_object()
        return context
    
class AdministratorProgramEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Program
    form_class = ProgramForm
    template_name = 'users/administrator/program/program_edit.html'

    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'administrator')

    def get_success_url(self):
        return reverse_lazy('administrator_program_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "The program was successfully updated.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There was an error updating the program. Please check the form and try again.")
        return super().form_invalid(form)
    

class AdministratorProgramPublishView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'users/administrator/program/program_publish_confirm.html'
    form_class = ProgramPublishForm
    success_url = reverse_lazy('administrator_program_list')

    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'administrator')

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

class AdministratorProgramUnpublishView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'users/administrator/program/program_unpublish_confirm.html'
    form_class = ProgramUnpublishForm
    success_url = reverse_lazy('administrator_program_list')

    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'administrator')

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
    

class AdministratorProgramCourseCreateView(CreateView):
    model = ProgramCourse
    form_class = ProgramCourseForm
    template_name = 'users/administrator/program/program_course_create.html'

    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'administrator')

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

class AdministratorEnrollmentCreateView(FormView):
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

class AdministratorEnrollmentListView(ListView):
    model = Enrollment
    template_name = 'users/administrator/enrollments/enrollment_list.html'
    context_object_name = 'enrollments'
    paginate_by = 20

    def get_queryset(self):
        queryset = Enrollment.objects.all().order_by('-enrollment_date')
        
        # Search
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(delivery__title__icontains=search_query) |
                Q(program__title__icontains=search_query) |
                Q(course__title__icontains=search_query)
            )

        # Filters
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        enrollment_type = self.request.GET.get('enrollment_type')
        if enrollment_type:
            if enrollment_type == 'delivery':
                queryset = queryset.filter(delivery__isnull=False)
            elif enrollment_type == 'program':
                queryset = queryset.filter(program__isnull=False)
            elif enrollment_type == 'course':
                queryset = queryset.filter(course__isnull=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['enrollment_type'] = self.request.GET.get('enrollment_type', '')
        
        # Calculate metrics
        all_enrollments = Enrollment.objects.all()
        context['total_enrollments'] = all_enrollments.count()
        context['active_enrollments'] = all_enrollments.filter(status='IN_PROGRESS').count()
        context['completed_enrollments'] = all_enrollments.filter(status='COMPLETED').count()
        
        return context
    
class AdministratorEnrollmentEditView(UpdateView):
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
# ======================= Notifications Views ================
# ============================================================

class AdministratorNotificationListView(TemplateView):
    template_name = 'users/administrator/notifications/notifications_course_list.html'