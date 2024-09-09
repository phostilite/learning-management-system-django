import logging
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
import rustici_software_cloud_v2 as scorm_cloud
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
import base64
import time
import tempfile
import shutil
import os
import json
import zipfile
import uuid
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rustici_software_cloud_v2.rest import ApiException
from django.views import View
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.core.files.base import File


from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken 

from courses.models import Course, LearningResource, ScormResource, Enrollment, ScormRegistration, Delivery
from .utils import course_id_is_valid
from users.models import Learner
from courses.models import Delivery


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import CourseDeliverySerializer, ScormRegistrationSerializer

User = get_user_model()

logger = logging.getLogger(__name__)

@csrf_exempt
def create_scorm_course(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            course_id = data['course_id']
            file_path = data['file_path']
            version = data['version']

            logger.info(f"create_scorm_course called with course_id: {course_id}, file_path: {file_path}, version: {version}")

            # Configure ScormCloud API
            config = scorm_cloud.Configuration()
            config.username = settings.CLOUDSCORM_APP_ID
            config.password = settings.CLOUDSCORM_SECRET_KEY
            scorm_cloud.Configuration().set_default(config)

            course_api = scorm_cloud.CourseApi()

            # Create and import the course to SCORM Cloud
            logger.info("Creating and importing the course to SCORM Cloud")
            job_id = course_api.create_upload_and_import_course_job(course_id, file=file_path)
            logger.debug(f"Job ID: {job_id}")

            # Check job status
            logger.info("Checking job status")
            job_result = course_api.get_import_job_status(job_id.result)
            while job_result.status == "RUNNING":
                logger.debug("Job status: RUNNING")
                time.sleep(1)
                job_result = course_api.get_import_job_status(job_id.result)

            if job_result.status == "ERROR":
                logger.error(f"Course import failed: {job_result.message}")
                return JsonResponse({'success': False, 'error': f"Course import failed: {job_result.message}"})

            response_data = {
                'success': True,
                'message': 'SCORM course created successfully on CloudSCORM',
                'scorm_course_id': course_id,
                'version': version,
                'web_path': job_result.import_result.web_path_to_course
            }
            logger.info(f"Response data: {response_data}")
            return JsonResponse(response_data)

        except Exception as e:
            logger.exception("An error occurred while creating the SCORM course on CloudSCORM.")
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

@csrf_exempt
def register_for_course(request):
    if request.method == 'POST':
        user = request.user
        course_delivery_id = request.POST.get('course_delivery_id')

        if not course_delivery_id:
            return JsonResponse({'error': 'Course delivery ID is required'}, status=400)

        try:
            course_delivery = Delivery.objects.get(id=course_delivery_id)
            enrollment, created = Enrollment.objects.get_or_create(
                user=user,
                course_delivery=course_delivery
            )

            if not created:
                return JsonResponse({'error': 'User is already enrolled in this course'}, status=400)

            # SCORM Cloud Registration
            config = scorm_cloud.Configuration()
            config.username = settings.CLOUDSCORM_APP_ID
            config.password = settings.CLOUDSCORM_SECRET_KEY
            scorm_cloud.Configuration().set_default(config)

            registration_api = scorm_cloud.RegistrationApi()

            scorm_resource = course_delivery.course.resources.filter(resource_type='SCORM').first().scorm_details

            if not scorm_resource:
                return JsonResponse({'error': 'No SCORM resource found for this course'}, status=400)

            scorm_registration_id = f"reg_{enrollment.id}"

            scorm_learner = scorm_cloud.LearnerSchema(
                id=str(user.id),
                first_name=user.first_name,
                last_name=user.last_name
            )

            registration = scorm_cloud.CreateRegistrationSchema(
                course_id=scorm_resource.scorm_course_id,
                learner=scorm_learner, 
                registration_id=scorm_registration_id,
            )

            registration_api.create_registration(registration)

            ScormRegistration.objects.create(
                enrollment=enrollment,
                scorm_registration_id=scorm_registration_id
            )

            return JsonResponse({
                'message': 'Registration successful',
                'enrollment_id': enrollment.id,
                'scorm_registration_id': scorm_registration_id,
            })

        except Delivery.DoesNotExist:
            return JsonResponse({'error': 'Course delivery not found'}, status=404)
        except Exception as e:
            logger.exception("Error during registration:")
            return JsonResponse({'error': str(e)}, status=500)

    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    

@require_http_methods(["GET", "POST"])
def scorm_cloud_operations(request):
    try:
        # ScormCloud Configuration
        config = scorm_cloud.Configuration()
        config.username = settings.CLOUDSCORM_APP_ID
        config.password = settings.CLOUDSCORM_SECRET_KEY
        scorm_cloud.Configuration().set_default(config)

        if request.method == 'GET':
            return get_launch_link(request)
        elif request.method == 'POST':
            return set_application_configuration(request)

    except Exception as e:
        logger.exception("Error in SCORM Cloud operations:")
        return JsonResponse({'error': str(e)}, status=500)
    
def get_launch_link(request):
    try:
        learner_id = request.GET.get('learner_id')
        registration_id = request.GET.get('registration_id')

        if not learner_id or not registration_id:
            raise ValueError("Learner ID and Registration ID are required.")

        # Validate learner and registration
        learner = Learner.objects.get(pk=learner_id)
        registration = ScormRegistration.objects.get(scorm_registration_id=registration_id, learner=learner)

        registration_api = scorm_cloud.RegistrationApi()

        # Build Launch Link
        launch_link_request = {
            "redirectOnExitUrl": "https://your-lms.com/exit",  # Replace with your actual exit URL
            "launchAuth": {
                "type": "vault"
            },
            "expiry": 3600, 
            "tracking": True
        }
        
        launch_link_response = registration_api.build_registration_launch_link(
            registration_id=str(registration.registration_id), 
            launch_link_request=launch_link_request,
        )
        
        return JsonResponse({'launch_link': launch_link_response.launch_link})

    except (Learner.DoesNotExist, ScormRegistration.DoesNotExist) as e:
        logger.error(f"Resource not found: {str(e)}")
        return JsonResponse({'error': str(e)}, status=404)
    except ValueError as e:
        logger.error(str(e))
        return JsonResponse({'error': str(e)}, status=400)
    except scorm_cloud.rest.ApiException as api_e:
        logger.error(f"ScormCloud API Error: {api_e}")
        return JsonResponse({'error': f'ScormCloud launch link generation failed: {api_e.reason}'}, status=500)

def set_application_configuration(request):
    try:
        app_management_api = scorm_cloud.ApplicationManagementApi()

        config_settings = {
            "settings": [
                {
                    "settingId": "PlayerLaunchType",
                    "value": "FRAMESET",
                    "explicit": True
                },
                {
                    "settingId": "PlayerScoLaunchType",
                    "value": "FRAMESET",
                    "explicit": True
                },
                {
                    "settingId": "LaunchAuthType",
                    "value": "vault",
                    "explicit": True
                }
            ]
        }

        response = app_management_api.set_application_configuration(config_settings)
        return JsonResponse({'message': 'Application configuration updated successfully'})

    except scorm_cloud.rest.ApiException as api_e:
        logger.error(f"ScormCloud API Error: {api_e}")
        return JsonResponse({'error': f'Failed to update application configuration: {api_e.reason}'}, status=500)
    

@method_decorator(csrf_exempt, name='dispatch')
class DeleteCourseView(View):
    def delete(self, request, course_id):
        try:
            # Configure SCORM Cloud client
            config = scorm_cloud.Configuration()
            config.username = settings.CLOUDSCORM_APP_ID
            config.password = settings.CLOUDSCORM_SECRET_KEY
            scorm_cloud.Configuration().set_default(config)
            
            # Initialize CourseApi
            course_api = scorm_cloud.CourseApi()
            
            # Delete the course
            course_api.delete_course(course_id)
            
            # Delete the course from local database
            try:
                scorm_course = Course.objects.get(course_id=course_id)
                scorm_course.delete()
                logger.info(f"Course with ID {course_id} has been successfully deleted from SCORM Cloud and local database.")
            except ObjectDoesNotExist:
                logger.warning(f"Course with ID {course_id} was deleted from SCORM Cloud but not found in local database.")
            
            return JsonResponse({"message": "Course deleted successfully from SCORM Cloud and local database"}, status=200)
        
        except ApiException as e:
            logger.error(f"API error occurred while deleting course {course_id} from SCORM Cloud: {str(e)}")
            return JsonResponse({"error": "API error occurred", "details": str(e)}, status=500)
        
        except ValueError as e:
            logger.error(f"Value error occurred while deleting course {course_id}: {str(e)}")
            return JsonResponse({"error": "Invalid course ID", "details": str(e)}, status=400)
        
        except Exception as e:
            logger.error(f"Unexpected error occurred while deleting course {course_id}: {str(e)}")
            return JsonResponse({"error": "An unexpected error occurred", "details": str(e)}, status=500)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        # Input validation
        if not email or not password:
            return Response({'error': 'Please provide both email and password.'}, status=status.HTTP_400_BAD_REQUEST)

        # User authentication
        user = authenticate(request, username=email, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)  
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            groups = list(user.groups.values_list('name', flat=True)) 

            try:
                learner = Learner.objects.get(user=user)
                learner_id = learner.id
            except Learner.DoesNotExist:
                learner_id = None  

            response_data = {
                'message': 'Login successful',
                'access': access_token,
                'refresh': refresh_token,
                'groups': groups,
                'learner_id': learner_id,
                'learner_name': user.get_full_name() if user.get_full_name() else None,
                'learner_email': user.email if user.email else None,
                'learner_phone': user.phone_number if user.phone_number else None,
                'learner_picture': request.build_absolute_uri(user.picture.url) if user.picture else None,
                'learner_date_joined': user.date_joined,
                'learner_gender': user.gender,
                'learner_timezone': user.timezone,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class EnrolledCoursesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        enrollments = Enrollment.objects.filter(user=request.user)
        course_deliveries = Delivery.objects.filter(enrollment__in=enrollments)
        serializer = CourseDeliverySerializer(course_deliveries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class GetScormRegistrationIDView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        course_delivery_id = request.query_params.get('course_delivery_id')

        if not course_delivery_id:
            return Response({"error": "course_delivery_id must be provided."}, status=status.HTTP_400_BAD_REQUEST)

        enrollment = get_object_or_404(Enrollment, user=request.user, course_delivery_id=course_delivery_id)
        scorm_registration = get_object_or_404(ScormRegistration, enrollment=enrollment)
        
        serializer = ScormRegistrationSerializer(scorm_registration)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RefreshTokenView(APIView):
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            return Response({"access_token": access_token})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)