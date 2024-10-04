import logging
import requests
from django.views.decorators.csrf import csrf_exempt

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .mixins import SupervisorRequiredMixin
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from formtools.wizard.views import SessionWizardView
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, DetailView, ListView, DeleteView, UpdateView
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import Http404
from django.http import JsonResponse

from announcements.models import Announcement, AnnouncementRead, AnnouncementRecipient
from announcements.forms import AnnouncementForm, AnnouncementRecipientForm

from .filters import AnnouncementFilter


from courses.forms import CourseForm, LearningResourceFormSet, ScormResourceForm
from courses.models import (Course, CourseCategory, Enrollment, LearningResource, ScormResource, Tag, Program)
from .api_client import upload_scorm_package, register_user_for_course

logger = logging.getLogger(__name__)

User = get_user_model()

@method_decorator(login_required, name='dispatch')
class SupervisorDashboardView(TemplateView):
    template_name = 'users/supervisor/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    


# ============================================================
# =================== Announcements Views ====================
# ============================================================
class SupervisorAnnouncementListView(LoginRequiredMixin, SupervisorRequiredMixin, ListView):
    template_name = 'users/supervisor/announcements/announcements_page.html'
    model = Announcement
    context_object_name = 'announcements'

    def get_queryset(self):
        user = self.request.user

        # Fetch announcements created by the supervisor
        supervisor_created = Announcement.objects.filter(author=user)

        # Fetch announcements for 'ALL' recipient type
        all_announcements = Announcement.objects.filter(
            recipients__recipient_type='ALL'
        )

        # Fetch 'SUPERVISOR' announcements
        supervisor_announcements = Announcement.objects.filter(
            recipients__recipient_type='SUPERVISOR'
        )

        # Fetch specific user announcements
        specific_user_announcements = Announcement.objects.filter(
            recipients__recipient_type='USER',
            recipients__specific_recipient__in=[user.username, user.email]
        )

        # Combine all announcements and ensure uniqueness
        combined_announcements = supervisor_created | all_announcements | supervisor_announcements | specific_user_announcements
        combined_announcements = combined_announcements.distinct().order_by('-publish_date')

        # Apply filters
        self.filterset = AnnouncementFilter(self.request.GET, queryset=combined_announcements)

        # Annotate each announcement with read status
        for announcement in self.filterset.qs:
            announcement.is_read = AnnouncementRead.objects.filter(announcement=announcement, user=user).exists()

        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        context['announcement_form'] = AnnouncementForm()
        context['recipient_form'] = AnnouncementRecipientForm()

        # Calculate metrics
        total_announcements = Announcement.objects.filter(author=self.request.user).count()
        active_announcements = Announcement.objects.filter(author=self.request.user, is_active=True).count()
        scheduled_announcements = Announcement.objects.filter(author=self.request.user, publish_date__gt=timezone.now()).count()
        
        total_reads = AnnouncementRead.objects.filter(announcement__author=self.request.user).count()
        avg_engagement_rate = (total_reads / total_announcements) * 100 if total_announcements > 0 else 0

        context['total_announcements'] = total_announcements
        context['active_announcements'] = active_announcements
        context['scheduled_announcements'] = scheduled_announcements
        context['avg_engagement_rate'] = avg_engagement_rate

        # Separate received announcements
        context['received_announcements'] = self.get_queryset().exclude(author=self.request.user)

        return context
    
    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        form_type = request.POST.get('form_type')
            
        if form_type == 'announcement_recipient':
            form = AnnouncementRecipientForm(request.POST)
            if form.is_valid():
                recipient = form.save(commit=False)
                recipient.announcement_id = request.POST.get('announcement_id')
                recipient.save()
                redirect_url = reverse('supervisor_announcements')
                return redirect(redirect_url)
            else:
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
        
class AnnouncementCreateView(LoginRequiredMixin, SupervisorRequiredMixin, View):
    def post(self, request):
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = self.request.user
            announcement.save()
            messages.success(request, 'Announcement created successfully')
            return redirect('supervisor_announcements')
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

class SupervisorAnnouncementDetailView(SupervisorRequiredMixin, LoginRequiredMixin, DetailView):
    model = Announcement
    template_name = 'users/supervisor/announcements/announcement_detail_page.html'
    context_object_name = 'announcement'

    def get_queryset(self):
        return Announcement.objects.filter(id=self.kwargs.get('pk'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        announcement = self.get_object()
        announcement_read = AnnouncementRead.objects.filter(user=self.request.user, announcement=announcement).exists()
        context['announcement_read'] = announcement_read
        return context
    
class SupervisorAnnouncementManageRecipientView(LoginRequiredMixin, SupervisorRequiredMixin, DetailView):
    model = Announcement
    template_name = 'users/supervisor/announcements/announcement_manage_recipient.html'
    context_object_name = 'recipients'

    def test_func(self):
        return self.request.user.groups.filter(name='supervisor').exists()

    def get_object(self):
        return get_object_or_404(Announcement, pk=self.kwargs.get('pk'))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        announcement = self.get_object()
        context['recipients'] = AnnouncementRecipient.objects.filter(announcement=announcement)
        context['announcement'] = announcement
        return context
    
class AnnouncementReadView(SupervisorRequiredMixin, LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            announcement = Announcement.objects.get(id=pk)
            announcement_read, created = AnnouncementRead.objects.get_or_create(user=request.user, announcement=announcement)
            if created:
                logger.info(f"Announcement {pk} marked as read by user {request.user.id}")
            else:
                logger.info(f"Announcement {pk} was already marked as read by user {request.user.id}")
            return redirect('supervisor_announcement_detail', pk=pk)
        except Announcement.DoesNotExist:
            logger.warning(f"Announcement {pk} not found for user {request.user.id}")
            return JsonResponse({'status': 'error', 'message': 'Announcement not found'}, status=404)
        except Exception as e:
            logger.error(f"Error marking announcement {pk} as read for user {request.user.id}: {e}")
            return JsonResponse({'status': 'error', 'message': 'An error occurred'}, status=500)

class SupervisorAnnouncementDeleteView(LoginRequiredMixin, SupervisorRequiredMixin, DeleteView):
    model = Announcement
    context_object_name = 'announcement'
    success_url = reverse_lazy('supervisor_announcementst')

    def test_func(self):
        return self.request.user.groups.filter(name='supervisor').exists()

    def get_object(self):
        return get_object_or_404(Announcement, pk=self.kwargs.get('pk'))
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({'success': True, 'redirect_url': str(self.success_url)})

class SupervisorAnnouncementUpdateView(LoginRequiredMixin, SupervisorRequiredMixin, UpdateView):
    model = Announcement
    form_class = AnnouncementForm
    context_object_name = 'announcement'
    success_url = reverse_lazy('supervisor_announcement_detail', kwargs={'pk': 'uuid:pk'})

    def test_func(self):
        return self.request.user.groups.filter(name='supervisor').exists()

    def get(self, request, *args, **kwargs):
        announcement = get_object_or_404(Announcement, pk=kwargs['pk'])
        data = {
            'title': announcement.title,
            'content': announcement.content,
            'priority': announcement.priority,
            'publish_date': announcement.publish_date.isoformat() if announcement.publish_date else None,
            'expiry_date': announcement.expiry_date.isoformat() if announcement.expiry_date else None,
        }
        return JsonResponse(data)

    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        announcement = get_object_or_404(Announcement, pk=kwargs['pk'])
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.save()
            redirect_url = reverse('supervisor_announcement_detail', kwargs={'pk': announcement.pk})
            return JsonResponse({'status': 'success', 'redirect_url': redirect_url})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)



# ============================================================
# =================== Notifications Views ====================
# ============================================================
class SupervisorNotificationListView(TemplateView):
    template_name = 'users/supervisor/notifications/notifications_course_list.html'
