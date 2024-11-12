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
from django.views.decorators.csrf import csrf_exempt
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

class MessageCenterView(TemplateView):
    template_name = 'users/communications/messages.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'total_messages': Message.objects.filter(thread__recipients__user=self.request.user).count(),
            'unread_messages': Message.objects.filter(thread__recipients__user=self.request.user, thread__recipients__is_read=False).count(),
            'flagged_messages': Message.objects.filter(thread__recipients__user=self.request.user, thread__recipients__is_starred=True).count(),
            'messages': Message.objects.filter(thread__recipients__user=self.request.user).order_by('-created_at')[:50]
        })
        return context

User = get_user_model()


# communications_view.py
@method_decorator(login_required, name='dispatch')
class SendMessageView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            form = MessageForm(data)  # Use MessageForm instead of NewMessageForm
            
            if form.is_valid():
                recipient_email = form.cleaned_data['recipient_email']
                subject = form.cleaned_data['subject']
                content = form.cleaned_data['content']
                
                try:
                    recipient = User.objects.get(email=recipient_email)
                except User.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': f'No user found with email {recipient_email}'
                    })

                with transaction.atomic():
                    thread = Thread.objects.create(subject=subject)
                    Message.objects.create(
                        thread=thread,
                        sender=request.user,
                        content=content
                    )
                    Recipient.objects.create(
                        thread=thread,
                        user=recipient,
                        is_read=False
                    )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Message sent successfully'
                })
            
            return JsonResponse({
                'success': False,
                'form_errors': form.errors
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON format'
            })
        except Exception as e:
            print(f"Error: {str(e)}")  # Add logging
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

class GetMessagesView(View):
    def get(self, request):
        messages = Message.objects.filter(
            thread__recipients__user=request.user
        ).select_related('sender', 'thread').order_by('-created_at')

        messages_data = [{
            'id': str(msg.id),
            'sender_name': msg.sender.get_full_name() or msg.sender.email,
            'subject': msg.thread.subject,
            'content': msg.content,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_read': msg.thread.recipients.filter(user=request.user).first().is_read,
            'is_starred': msg.thread.recipients.filter(user=request.user).first().is_starred
        } for msg in messages]

        return JsonResponse({'success': True, 'messages': messages_data})

class GetMessageDetailsView(View):
    def get(self, request):
        message_id = request.GET.get('id')
        try:
            message = Message.objects.select_related(
                'sender', 'thread'
            ).get(id=message_id)
            
            recipient = message.thread.recipients.filter(user=request.user).first()
            if recipient:
                recipient.is_read = True
                recipient.save()

            return JsonResponse({
                'success': True,
                'sender_name': message.sender.get_full_name() or message.sender.email,
                'subject': message.thread.subject,
                'content': message.content,
                'created_at': message.created_at.strftime('%Y-%m-%d %H:%M')
            })
        except Message.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Message not found'})

class ToggleStarMessageView(View):
    def post(self, request):
        message_id = request.POST.get('id')
        try:
            message = Message.objects.get(id=message_id)
            recipient = message.thread.recipients.get(user=request.user)
            recipient.is_starred = not recipient.is_starred
            recipient.save()
            return JsonResponse({'success': True})
        except (Message.DoesNotExist, Recipient.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Message not found'})
        
        
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
    
class NewMessageView(TemplateView, View):
    template_name = 'users/communications/new_message.html'

    def get(self, request):
        form = NewMessageForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = NewMessageForm(request.POST)
        if form.is_valid():
            try:
                recipient_email = form.cleaned_data['recipient_email']
                subject = form.cleaned_data['subject']
                content = form.cleaned_data['content']

                recipient = get_user_model().objects.get(email=recipient_email)
                
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
                
                return redirect(reverse('message_center'))
            except get_user_model().DoesNotExist:
                form.add_error('recipient_email', _('Recipient not found.'))
            except Exception as e:
                return render(request, self.template_name, {'form': form, 'error': str(e)})
        
        return render(request, self.template_name, {'form': form})