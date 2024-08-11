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

from courses.forms import CourseBasicInfoForm, LearningResourceFormSet, ScormResourceForm
from courses.models import (Attendance, Course, CourseCategory, CourseDelivery, 
                            Enrollment, Feedback, LearningResource, ScormResource)
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
    
@method_decorator(login_required, name='dispatch')
class AdministratorLearnerListView(ListView):
    template_name = 'users/administrator/learners.html'
    context_object_name = 'learners'

    def get_queryset(self):
        pass

@method_decorator(login_required, name='dispatch')
class AdministratorFacilitatorListView(ListView):
    template_name = 'users/administrator/facilitators.html'
    context_object_name = 'facilitators'

    def get_queryset(self):
        pass

@method_decorator(login_required, name='dispatch')
class AdministratorSupervisorListView(ListView):
    template_name = 'users/administrator/supervisors.html'
    context_object_name = 'supervisors'

    def get_queryset(self):
        pass

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
                                    scorm_course_id=api_response['id'],
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