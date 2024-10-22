# Standard library imports
import json
import logging
from datetime import timedelta

# Third-party imports
import requests
from formtools.wizard.views import SessionWizardView
from rest_framework import permissions, status
from rest_framework.permissions import BasePermission, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.views import FilterView

# Django imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.forms import formset_factory
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import (CreateView, DeleteView, DetailView, FormView,
                                  ListView, TemplateView, UpdateView)

from communications.models import Message, Recipient, Thread
from .forms import NewMessageForm

class CommunicationMessageListView( TemplateView):
    template_name = 'users/communications/messages.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class MessageCenterView( TemplateView):
    template_name = 'users/communications/messages.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'total_messages': Message.objects.filter(thread__recipients__user=self.request.user).count(),
            'unread_messages': Message.objects.filter(thread__recipients__user=self.request.user, thread__recipients__is_read=False).count(),
            'flagged_messages': Message.objects.filter(thread__recipients__user=self.request.user, thread__recipients__is_starred=True).count(),
        })
        return context

@method_decorator(login_required, name='dispatch')
class SendMessageView(View):
    @transaction.atomic
    def post(self, request):
        try:    
            subject = request.POST.get('subject')
            content = request.POST.get('message')
            recipient_id = request.POST.get('recipient')
            
            recipient = get_user_model().objects.get(id=recipient_id)
            
            thread = Thread.objects.create(subject=subject)
            message = Message.objects.create(
                thread=thread,
                sender=request.user,
                content=content
            )
            Recipient.objects.create(
                thread=thread,
                user=recipient
            )
            
            return JsonResponse({'success': True, 'message': _('Message sent successfully.')})
        except get_user_model().DoesNotExist:
            return JsonResponse({'success': False, 'error': _('Recipient not found.')})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@method_decorator(login_required, name='dispatch')
class GetMessagesView(View):
    def get(self, request):
        messages = Message.objects.filter(
            thread__recipients__user=request.user
        ).select_related('sender', 'thread').order_by('-created_at')[:50]
        
        message_list = [{
            'id': msg.id,
            'sender_name': msg.sender.get_full_name(),
            'subject': msg.thread.subject,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_read': msg.thread.recipients.filter(user=request.user).first().is_read,
            'is_starred': msg.thread.recipients.filter(user=request.user).first().is_starred,
        } for msg in messages]
        
        return JsonResponse({'messages': message_list})

@method_decorator(login_required, name='dispatch')
class GetMessageDetailsView(View):
    def get(self, request):
        try:
            message_id = request.GET.get('id')
            message = get_object_or_404(Message.objects.select_related('sender', 'thread'), id=message_id)
            
            recipient = get_object_or_404(Recipient, thread=message.thread, user=request.user)
            if not recipient.is_read:
                recipient.is_read = True
                recipient.save()
            
            return JsonResponse({
                'success': True,
                'sender_name': message.sender.get_full_name(),
                'recipient_name': message.thread.recipients.exclude(user=message.sender).first().user.get_full_name(),
                'subject': message.thread.subject,
                'content': message.content,
                'created_at': message.created_at.strftime('%Y-%m-%d %H:%M'),
                'is_starred': recipient.is_starred,
            })
        except Http404:
            return JsonResponse({'success': False, 'error': _('Message not found.')})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@method_decorator(login_required, name='dispatch')
class ToggleStarMessageView(View):
    def post(self, request):
        try:
            message_id = request.POST.get('id')
            message = get_object_or_404(Message, id=message_id)
            recipient = get_object_or_404(Recipient, thread=message.thread, user=request.user)
            recipient.is_starred = not recipient.is_starred
            recipient.save()
            return JsonResponse({'success': True, 'is_starred': recipient.is_starred})
        except Http404:
            return JsonResponse({'success': False, 'error': _('Message not found.')})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@method_decorator(login_required, name='dispatch')
class GetUserListView(View):
    def get(self, request):
        query = request.GET.get('q', '')
        users = get_user_model().objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
        ).values('id', 'username', 'first_name', 'last_name')[:10]
        return JsonResponse({'users': list(users)})
    
class NewMessageView( TemplateView, View):
    template_name = 'users/communications/new_message.html'

    def get(self, request):
        form = NewMessageForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = NewMessageForm(request.POST)
        if form.is_valid():
            recipient = form.cleaned_data['recipient']
            subject = form.cleaned_data['subject']
            content = form.cleaned_data['content']
            
            thread = Thread.objects.create(subject=subject)
            message = Message.objects.create(
                thread=thread,
                sender=request.user,
                content=content
            )
            Recipient.objects.create(
                thread=thread,
                user=recipient
            )
            
            messages.success(request, _('Message sent successfully.'))
            return redirect(reverse('message_center'))
        
        return render(request, self.template_name, {'form': form})