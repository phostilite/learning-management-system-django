import requests
from django.conf import settings
import logging
import json

logger = logging.getLogger(__name__)

import urllib.parse

def create_scorm_course(course_id, file_path, version):
    logger.info(f"create_scorm_course called with course_id: {course_id}, file_path: {file_path}, version: {version}")
    try:
        data = {
            'course_id': course_id,
            'file_path': file_path,
            'version': version
        }
        logger.debug(f"Request data: {data}")

        response = requests.post(
            'http://127.0.0.1:8000/api/create_scorm_course/',
            data=json.dumps(data),
            headers={'Content-Type': 'application/json'},
            timeout=300,
        )
        response.raise_for_status()
        response_data = response.json()
        logger.info(f"Response data: {response_data}")
        return response_data
    except requests.RequestException as e:
        logger.exception(f"Error calling create_scorm_course API for course {course_id}:")
        return {'success': False, 'error': str(e)}
    
def register_user_for_course(user_id, course_id):
    logger.info(f"register_user_for_course called with user_id: {user_id}, course_id: {course_id}")
    try:
        data = {'learner_id': user_id, 'course_id': course_id}
        logger.debug(f"Request data: {data}")

        response = requests.post(
            f'{settings.SCORM_API_BASE_URL}/api/register/',
            data=data,
            timeout=30,
        )
        response.raise_for_status()
        logger.info(f"User {user_id} successfully registered for course {course_id}")
        return {'success': True}
    except requests.RequestException as e:
        logger.exception(f"Error registering user {user_id} for course {course_id}:")
        return {'success': False, 'error': str(e)}