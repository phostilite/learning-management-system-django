import logging
import requests


from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from .mixins import FacilitatorRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from formtools.wizard.views import SessionWizardView
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView, DetailView, ListView
from django.http import Http404
from django.http import JsonResponse


from announcements.models import Announcement, AnnouncementRead

from courses.forms import CourseForm, LearningResourceFormSet, ScormResourceForm
from courses.models import (Course, CourseCategory, Enrollment, LearningResource, ScormResource, Tag, Program)
from .api_client import upload_scorm_package, register_user_for_course

logger = logging.getLogger(__name__)

User = get_user_model()

@method_decorator(login_required, name='dispatch')
class FacilitatorDashboardView(TemplateView):
    template_name = 'users/facilitator/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class FacilitatorNotificationListView(TemplateView):
    template_name = 'users/facilitator/notifications/notifications_course_list.html'



# ============================================================
# =================== Announcements Views ====================
# ============================================================
class AnnouncementListView(FacilitatorRequiredMixin, LoginRequiredMixin, ListView):
    model = Announcement
    template_name = 'users/facilitator/announcements/announcements_page.html'
    context_object_name = 'announcements'

    def get_queryset(self):
        user = self.request.user

        # Fetch announcements for 'ALL' recipient type
        all_announcements = Announcement.objects.filter(
            recipients__recipient_type='ALL'
        ).distinct()

        # Initialize combined announcements with 'ALL' announcements
        combined_announcements = all_announcements

        # Check if user is in 'facilitator' group and fetch 'FACILITATOR' announcements
        if user.groups.filter(name='facilitator').exists():
            facilitator_announcements = Announcement.objects.filter(
                recipients__recipient_type='FACILITATOR'
            ).distinct()
            combined_announcements = combined_announcements | facilitator_announcements

        # Fetch specific user announcements
        specific_user_announcements = Announcement.objects.filter(
            recipients__recipient_type='USER',
            recipients__specific_recipient__in=[user.username, user.email]
        ).distinct()

        # Combine all announcements and ensure uniqueness
        combined_announcements = combined_announcements | specific_user_announcements
        combined_announcements = combined_announcements.distinct()

        # Annotate each announcement with read status
        for announcement in combined_announcements:
            announcement.is_read = AnnouncementRead.objects.filter(announcement=announcement, user=user).exists()

        return combined_announcements

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print(f"Context data: {context}")
        return context

class AnnouncementDetailView(FacilitatorRequiredMixin, LoginRequiredMixin, DetailView):
    model = Announcement
    template_name = 'users/facilitator/announcements/announcement_detail.html'
    context_object_name = 'announcement'

    def get_queryset(self):
        return Announcement.objects.filter(id=self.kwargs.get('pk'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        announcement = self.get_object()
        announcement_read = AnnouncementRead.objects.filter(user=self.request.user, announcement=announcement).exists()
        context['announcement_read'] = announcement_read
        return context
    
class AnnouncementReadView(FacilitatorRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            announcement = Announcement.objects.get(id=pk)
            announcement_read, created = AnnouncementRead.objects.get_or_create(user=request.user, announcement=announcement)
            if created:
                logger.info(f"Announcement {pk} marked as read by user {request.user.id}")
            else:
                logger.info(f"Announcement {pk} was already marked as read by user {request.user.id}")
            return redirect('facilitator_announcement_detail', pk=pk)
        except Announcement.DoesNotExist:
            logger.warning(f"Announcement {pk} not found for user {request.user.id}")
            return JsonResponse({'status': 'error', 'message': 'Announcement not found'}, status=404)
        except Exception as e:
            logger.error(f"Error marking announcement {pk} as read for user {request.user.id}: {e}")
            return JsonResponse({'status': 'error', 'message': 'An error occurred'}, status=500)
  




