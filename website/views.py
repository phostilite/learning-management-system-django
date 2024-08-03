import logging
from django.shortcuts import render
from django.http import HttpResponseServerError

logger = logging.getLogger(__name__)

def landing_page(request):
    try:
        return render(request, 'website/landing_page.html')
    except Exception as e:
        logger.error(f"Error rendering landing page: {e}")
        return HttpResponseServerError("An error occurred while processing your request.")

def about_page(request):
    try:
        return render(request, 'website/about_page.html')
    except Exception as e:
        logger.error(f"Error rendering about page: {e}")
        return HttpResponseServerError("An error occurred while processing your request.")

def contact_page(request):
    try:
        return render(request, 'website/contact_page.html')
    except Exception as e:
        logger.error(f"Error rendering contact page: {e}")
        return HttpResponseServerError("An error occurred while processing your request.")