from django.conf import settings
from django.shortcuts import render
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.MAINTENANCE_MODE:
            if not request.user.is_staff and settings.MAINTENANCE_BYPASS_QUERY_STRING not in request.GET:
                if request.path != reverse('login'):
                    logger.info(f"Maintenance mode active: Redirected {request.user} from {request.path}")
                    return render(request, 'maintenance/maintenance.html', status=503)
            else:
                logger.info(f"Maintenance mode bypassed: {request.user} accessed {request.path}")

        response = self.get_response(request)
        return response