import logging
from django.views import View
import requests
import json

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
from django.db.models import Count, Q
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import BasePermission
from django.db import transaction
from django.views.decorators.http import require_http_methods

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import Group
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.views.generic import FormView

from courses.forms import CourseBasicInfoForm, LearningResourceFormSet, ScormResourceForm, LearningResourceForm, CourseDeliveryForm, EnrollmentForm
from courses.models import (Attendance, Course, CourseCategory, CourseDelivery, 
                            Enrollment, Feedback, LearningResource, ScormResource)
from users.forms import LearnerCreationForm
from users.models import Learner, Facilitator, Supervisor
from .api_client import upload_scorm_package, register_user_for_course, create_scormhub_course

logger = logging.getLogger(__name__)

User = get_user_model()

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
    
class AdministratorCertificateListView(TemplateView):
    template_name = 'users/administrator/certificates.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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

@method_decorator(login_required, name='dispatch')
class AdministratorCourseCategoryListView(ListView):
    model = CourseCategory
    template_name = 'users/administrator/course/categories.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return CourseCategory.objects.all()
    
@method_decorator(login_required, name='dispatch')
class AdministratorCourseEnrollmentListView(ListView):
    model = Enrollment
    template_name = 'users/administrator/course/enrollments.html'
    context_object_name = 'enrollments'

    def get_queryset(self):
        return Enrollment.objects.all()
    
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
                learner = Learner.objects.create(user=user, token=scorm_data['token'])
                logger.info(f"Learner created with SCORM token: {learner.token}")
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

class CourseCreationWizard(SessionWizardView):
    file_storage = FileSystemStorage(location=settings.MEDIA_ROOT)
    form_list = [
        ('basic_info', CourseBasicInfoForm),
        ('learning_resources', LearningResourceFormSet),
    ]
    template_name = 'users/administrator/course/create.html'

    def get_form_initial(self, step):
        logger.debug(f"get_form_initial called for step: {step}")
        initial = super().get_form_initial(step)
        if step == 'basic_info':
            initial['created_by'] = self.request.user.id
        logger.debug(f"Initial data for {step}: {initial}")
        return initial

    def get_form(self, step=None, data=None, files=None):
        form = super().get_form(step, data, files)
        logger.debug(f"get_form called for step: {step}")
        logger.debug(f"Form data: {data}")
        logger.debug(f"Form files: {files}")
        return form

    def process_step(self, form):
        logger.debug(f"process_step called for step: {self.steps.current}")
        if self.steps.current == 'learning_resources':
            for resource_form in form:
                logger.debug(f"Resource form data: {resource_form.cleaned_data}")
                if resource_form.is_valid() and resource_form.cleaned_data.get('resource_type') == 'SCORM':
                    logger.debug(f"SCORM resource detected: {resource_form.prefix}")
                    logger.debug(f"SCORM file: {resource_form.cleaned_data.get('content')}")
                    logger.debug(f"SCORM details: {resource_form.cleaned_data.get('scorm_details')}")
        return super().process_step(form)

    @transaction.atomic
    def done(self, form_list, **kwargs):
        logger.info("Starting course creation process")
        try:
            basic_info_form = form_list[0]
            logger.debug(f"Basic info form data: {basic_info_form.cleaned_data}")
            basic_info = basic_info_form.save(commit=False)
            basic_info.created_by = self.request.user
            basic_info.save()
            logger.info(f"Basic course info saved: {basic_info.id}")

            # Create course on SCORMHub API
            scormhub_course_id = create_scormhub_course(basic_info.title, basic_info.description)
            logger.info(f"Course created on SCORMHub with ID: {scormhub_course_id}")

            learning_resource_formset = form_list[1]
            for resource_form in learning_resource_formset:
                if resource_form.is_valid() and not resource_form.cleaned_data.get('DELETE', False):
                    resource = resource_form.save(commit=False)
                    resource.course = basic_info
                    resource.save()
                    logger.info(f"Learning resource saved: {resource.id}, Type: {resource.resource_type}")

                    if resource.resource_type == 'SCORM':
                        logger.info(f"Processing SCORM resource: {resource.id}")
                        scorm_details = resource_form.cleaned_data.get('scorm_details')
                        if scorm_details and resource.content:
                            file = resource.content
                            logger.info(f"SCORM file path: {file}")
                            logger.info(f"Calling upload_scorm_package API for resource: {resource.id}")
                            api_response = upload_scorm_package(
                                scormhub_course_id,  
                                file,
                            )
                            logger.info(f"API response received: {api_response}")
                            if isinstance(api_response, dict) and 'id' in api_response:
                                logger.info(f"SCORM course created successfully: {api_response['id']}")
                                ScormResource.objects.create(
                                    learning_resource=resource,
                                    scorm_course_id=api_response['course'],
                                    scorm_package_id=api_response['id'],
                                    version=api_response.get('version', scorm_details['version']),
                                    web_path=api_response.get('launch_path', '')
                                )
                                logger.info(f"ScormResource created for: {resource.id}")
                            else:
                                error_message = api_response.get('error') if isinstance(api_response, dict) else "Unexpected API response format"
                                logger.error(f"Failed to create SCORM course: {error_message}")
                                raise Exception(f"Failed to create SCORM course: {error_message}")
                        else:
                            logger.warning(f"SCORM resource {resource.id} missing scorm_details or content")

            logger.info("Course creation process completed successfully")
            messages.success(self.request, 'Course created successfully!')
            return redirect('course_detail', pk=basic_info.pk)

        except Exception as e:
            logger.exception("Error during course creation:")
            messages.error(self.request, f"An error occurred while creating the course: {str(e)}")
            return redirect('course_list')
        
    def create_scormhub_course(self, title, description):
        """
        Create a course on SCORMHub API and return the course ID.
        """
        url = f'{settings.SCORM_API_BASE_URL}/api/courses/'
        token = f'{settings.SCORM_API_TOKEN}'
        headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
        data = {
            'title': title,
            'description': description
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            course_data = response.json()
            return course_data['id']
        except requests.RequestException as e:
            logger.error(f"Failed to create course on SCORMHub: {str(e)}")
            raise Exception("Failed to create course on SCORMHub API")

def create_course(request):
    logger.info("create_course view called")
    return CourseCreationWizard.as_view()(request)

def list_courses(request):
    try:
        courses = Course.objects.filter(created_by=request.user)
        logger.info(f"Fetched {len(courses)} courses for user {request.user.id}")
        return render(request, 'users/administrator/course/list.html', {'courses': courses})
    except Exception as e:
        logger.exception("Error fetching course list:")
        messages.error(request, f"An error occurred while fetching the course list: {str(e)}")
        return render(request, 'users/administrator/course/list.html', {'courses': []})
    
@method_decorator(login_required, name='dispatch')
class AdministratorCourseDeliveryListView(ListView):
    model = CourseDelivery
    template_name = 'users/administrator/course/deliveries.html'
    context_object_name = 'deliveries'

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        self.course = get_object_or_404(Course, id=course_id)
        return CourseDelivery.objects.filter(course=self.course)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.course
        return context
    
@require_POST
def add_learning_resource(request, course_id):
    course = get_object_or_404(Course, id=course_id, created_by=request.user)
    form = LearningResourceForm(request.POST, request.FILES)
    if form.is_valid():
        resource = form.save(commit=False)
        resource.course = course

        if resource.resource_type == 'SCORM':
            try:
                scorm_course_id = create_scormhub_course(resource.title, resource.description)
                upload_result =  upload_scorm_package(scorm_course_id, resource.content)

                if upload_result.get('success'):
                    try:
                        ScormResource.objects.create(
                            learning_resource=resource,
                            scorm_course_id=upload_result['id'],
                            version=upload_result.get('version', upload_result['version']),
                            web_path=upload_result.get('launch_path', '')
                        )
                    except Exception as e:
                        messages.error(request, f"Error saving SCORM package details: {str(e)}")
                        return render(request, 'add_learning_resource.html', {'form': form})
                else:
                    messages.error(request, f"Failed to upload SCORM package: {upload_result.get('error', 'Unknown error')}")
                    return render(request, 'add_learning_resource.html', {'form': form})
            except Exception as e:
                messages.error(request, f"Error processing SCORM package: {str(e)}")
        resource.save()
        return JsonResponse({
            'status': 'success',
            'message': 'Resource added successfully',
            'resource': {
                'id': resource.id,
                'title': resource.title,
                'resource_type': resource.get_resource_type_display(),
                'order': resource.order,
                'updated_at': resource.updated_at.strftime('%B %d, %Y')
            }
        })
    else:
        return JsonResponse({
            'status': 'error',
            'errors': form.errors
        }, status=400)
    
@method_decorator(login_required, name='dispatch')
class CourseDetailView(DetailView):
    model = Course
    template_name = 'users/administrator/course/detail.html'
    context_object_name = 'course'

    def get_object(self, queryset=None):
        try:
            course = super().get_object(queryset)
            if course.created_by != self.request.user:
                raise Http404("Course not found.")
            logger.info(f"Fetched course details for course {course.pk} by user {self.request.user.id}")
            return course
        except Http404:
            logger.warning(f"Course {self.kwargs['pk']} not found for user {self.request.user.id}")
            messages.error(self.request, "Course not found.")
            raise
        except Exception as e:
            logger.exception("Error fetching course details:")
            messages.error(self.request, f"An error occurred while fetching the course details: {str(e)}")
            raise Http404("An error occurred while fetching the course details.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = LearningResourceForm()  
        course = self.object

        # Fetch learning resources
        context['learning_resources'] = LearningResource.objects.filter(course=course).order_by('order')

        # Fetch course deliveries with enrollment counts
        deliveries = CourseDelivery.objects.filter(course=course).annotate(
            total_enrollments=Count('enrollment'),
            active_enrollments=Count('enrollment', filter=Q(enrollment__status__in=['ENROLLED', 'IN_PROGRESS']))
        ).order_by('-start_date')

        context['course_deliveries'] = deliveries

        # Calculate total enrollments across all deliveries
        context['total_enrollments'] = sum(delivery.total_enrollments for delivery in deliveries)
        context['total_active_enrollments'] = sum(delivery.active_enrollments for delivery in deliveries)

        # Fetch recent enrollments
        context['recent_enrollments'] = Enrollment.objects.filter(
            course_delivery__course=course
        ).select_related('user', 'course_delivery').order_by('-enrollment_date')[:10]

        # Calculate some statistics
        context['total_resources'] = context['learning_resources'].count()
        context['total_deliveries'] = deliveries.count()

        context['SCORM_API_BASE_URL'] = settings.SCORM_API_BASE_URL
        context['SCORM_PLAYER_USER_ID'] = self.request.user.scorm_profile.scorm_player_id
        context['SCORM_PLAYER_API_TOKEN'] = self.request.user.scorm_profile.token
        
        
        return context
        

class IsInAdministratorGroup(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name='administrator').exists()

class AdministratorCourseDeleteView(APIView):
    permission_classes = [IsInAdministratorGroup]

    def get(self, request, course_id):
        """
        Provide information about what will be deleted if the course is removed.
        """
        logger.info(f"GET request received for course_id: {course_id}")
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            logger.error(f"Course with id {course_id} not found")
            return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

        # Gather related data
        deliveries = CourseDelivery.objects.filter(course=course)
        enrollments = Enrollment.objects.filter(course_delivery__course=course)
        resources = LearningResource.objects.filter(course=course)
        scorm_resources = ScormResource.objects.filter(learning_resource__course=course)

        logger.info(f"Related data for course_id {course_id}: {deliveries.count()} deliveries, {enrollments.count()} enrollments, {resources.count()} resources, {scorm_resources.count()} SCORM packages")

        warning_message = f"""
        Warning: Deleting this course will remove the following:
        - The course from this LMS
        - The course and all associated SCORM packages from the SCORM player
        - {deliveries.count()} course deliveries
        - {enrollments.count()} user enrollments
        - {resources.count()} learning resources
        - {scorm_resources.count()} SCORM packages

        This action cannot be undone. Are you sure you want to proceed?
        """

        logger.info(f"GET request for course_id {course_id} completed successfully")
        return Response({"warning": warning_message}, status=status.HTTP_200_OK)

    def delete(self, request, course_id):
        """
        Delete the course and all associated data from both the current LMS and SCORM player.
        """
        logger.info(f"DELETE request received for course_id: {course_id}")
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            logger.error(f"Course with id {course_id} not found")
            return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

        # Start a transaction to ensure all deletions are successful or none are applied
        with transaction.atomic():
            logger.info(f"Transaction started for deleting course_id {course_id}")
            # Delete all SCORM packages associated with the course
            learning_resources = LearningResource.objects.filter(course=course, resource_type='SCORM')
            for resource in learning_resources:
                try:
                    scorm_resource = ScormResource.objects.get(learning_resource=resource)
                    self.delete_scorm_package_from_scorm_player(scorm_resource.scorm_course_id)
                except ScormResource.DoesNotExist:
                    logger.warning(f"SCORM resource not found for learning resource {resource.id}")

            # Delete the course and all related data from our local database
            course.delete()
            logger.info(f"Course and all related data for course_id {course_id} deleted successfully")

        logger.info(f"Transaction completed for deleting course_id {course_id}")
        return Response({"message": "Course and all associated data have been successfully deleted from the LMS and SCORM player."}, status=status.HTTP_200_OK)

    def delete_scorm_package_from_scorm_player(self, scorm_course_id):
        """
        Delete a SCORM package from the SCORM player API.
        """
        logger.info(f"Deleting SCORM package with id {scorm_course_id} from SCORM player API")
        scorm_api_url = f"{settings.SCORM_API_BASE_URL}/api/scorm-packages/{scorm_course_id}/"
        headers = {"Authorization": f"Token {settings.SCORM_API_TOKEN}"}

        try:
            response = requests.delete(scorm_api_url, headers=headers)
            if response.status_code != 204:
                logger.error(f"Failed to delete SCORM package {scorm_course_id} from SCORM player API. Status: {response.status_code}")
                raise Exception("Failed to delete SCORM package from SCORM player API")
        except requests.RequestException as e:
            logger.error(f"Error deleting SCORM package {scorm_course_id} from SCORM player API: {str(e)}")
            raise
    

class AdministratorCourseDeliveryCreateView(CreateView):
    model = CourseDelivery
    form_class = CourseDeliveryForm
    template_name = 'users/administrator/course/create_delivery.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        course_id = self.kwargs.get('course_id')
        self.course = get_object_or_404(Course, id=course_id)
        kwargs['course'] = self.course
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.course
        return context

    def get_success_url(self):
        return reverse_lazy('administrator_course_delivery_list', kwargs={'course_id': self.course.id})
    

class AdministratorCourseDeliveryDetailView(DetailView):
    model = CourseDelivery
    template_name = 'users/administrator/course/delivery_detail.html'

    def get_object(self):
        course_id = self.kwargs.get('course_id')
        delivery_id = self.kwargs.get('delivery_id')
        return CourseDelivery.objects.get(course_id=course_id, id=delivery_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.object.course
        context['enrollments'] = Enrollment.objects.filter(course_delivery=self.object)
        return context

    def get_success_url(self):
        return reverse_lazy('administrator_course_delivery_list', kwargs={'course_id': self.object.course.id})
    

class AdministratorCourseDeliveryEnrollView(FormView):
    template_name = 'users/administrator/course/enroll_learners.html'
    form_class = EnrollmentForm

    def get_success_url(self):
        return reverse_lazy('administrator_course_delivery_detail', kwargs={
            'course_id': self.kwargs['course_id'],
            'delivery_id': self.kwargs['delivery_id']
        })

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['course_delivery'] = self.get_course_delivery()
        return kwargs

    def get_course_delivery(self):
        course = get_object_or_404(Course, id=self.kwargs['course_id'])
        return get_object_or_404(CourseDelivery, id=self.kwargs['delivery_id'], course=course)

    def form_valid(self, form):
        enrollments = form.save()
        enrolled_count = len(enrollments)
        if enrolled_count > 0:
            messages.success(self.request, f'{enrolled_count} learner(s) have been enrolled in {self.get_course_delivery().title}')
        else:
            messages.info(self.request, "No new learners were enrolled. They may already be enrolled in this course delivery.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, id=self.kwargs['course_id'])
        context['course_delivery'] = self.get_course_delivery()
        return context