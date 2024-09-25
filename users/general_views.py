import logging
from django.views.generic import TemplateView
from django.shortcuts import render
from django.http import HttpResponseServerError

logger = logging.getLogger(__name__)

class SessionExpiredView(TemplateView):
    template_name = 'session/session_expired.html'

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return HttpResponseServerError("An internal server error occurred.")
