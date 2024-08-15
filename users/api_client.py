import requests
from django.conf import settings
import logging
import json
import time

logger = logging.getLogger(__name__)

def upload_scorm_package(course_id, file):
    logger.info(f"create_scorm_course called with course_id: {course_id}, file: {file}.")
    
    base_url = f'{settings.SCORM_API_BASE_URL}'
    token = f'{settings.SCORM_API_TOKEN}'
    headers = {
        'Authorization': f'Token {token}',
    }

    try:
        # Step 1: Upload the package
        upload_url = f'{base_url}/api/scorm-packages/upload_package/'
        data = {
            'course_id': course_id,
        }
        files = {
            'file': file
        }
        logger.debug(f"Upload request data: {data}")

        upload_response = requests.post(
            upload_url,
            data=data,
            files=files,
            headers=headers,
            timeout=300,
        )
        upload_response.raise_for_status()
        upload_data = upload_response.json()
        logger.info(f"Upload response data: {upload_data}")

        # Step 2: Check the status
        task_id = upload_data['task_id']
        status_url = f'{base_url}/api/scorm-packages/check_status/?task_id={task_id}'
        
        max_retries = 10
        retry_delay = 5  # seconds

        for _ in range(max_retries):
            status_response = requests.get(status_url, headers=headers, timeout=30)
            status_response.raise_for_status()
            status_data = status_response.json()
            logger.info(f"Status check response: {status_data}")

            if status_data.get('status') == 'ready':
                return status_data

            time.sleep(retry_delay)

        logger.warning(f"Package processing did not complete after {max_retries} retries.")
        return {'success': False, 'error': 'Package processing timeout'}

    except requests.RequestException as e:
        logger.exception(f"Error in create_scorm_course for course {course_id}:")
        return {'success': False, 'error': str(e)}
    
def create_scormhub_course(title, description):
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