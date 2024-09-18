# support/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages
from django.core.paginator import Paginator
from .models import SupportTicket, FAQ, SupportCategory, TicketResponse, Feedback, Learner
from .forms import (
    LoginForm, LearnerCreationForm, SupportTicketForm, TicketResponseForm,
    FeedbackForm, FAQSearchForm, SupportCategoryForm, FAQForm
)
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'support/login.html'

class LearnerSignUpView(CreateView):
    model = User
    form_class = LearnerCreationForm
    template_name = 'support/learner_signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        Learner.objects.create(user=user)
        messages.success(self.request, 'Account created successfully. You can now log in.')
        return super().form_valid(form)

class TicketListView(LoginRequiredMixin, ListView):
    model = SupportTicket
    template_name = 'support/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(created_by=self.request.user)
        
        status = self.request.GET.get('status')
        priority = self.request.GET.get('priority')
        
        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = SupportTicket.STATUS_CHOICES
        context['priority_choices'] = SupportTicket.PRIORITY_CHOICES
        return context

class TicketCreateView(LoginRequiredMixin, CreateView):
    model = SupportTicket
    form_class = SupportTicketForm
    template_name = 'support/ticket_create.html'
    success_url = reverse_lazy('ticket_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Ticket created successfully.')
        return super().form_valid(form)

class TicketDetailView(LoginRequiredMixin, DetailView):
    model = SupportTicket
    template_name = 'support/ticket_detail.html'
    context_object_name = 'ticket'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['response_form'] = TicketResponseForm()
        return context

class TicketUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = SupportTicket
    fields = ['status', 'priority', 'assigned_to']
    template_name = 'support/ticket_update.html'
    success_url = reverse_lazy('ticket_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Ticket updated successfully.')
        return super().form_valid(form)

class TicketResponseCreateView(LoginRequiredMixin, CreateView):
    model = TicketResponse
    form_class = TicketResponseForm
    template_name = 'support/ticket_response_create.html'

    def form_valid(self, form):
        ticket = get_object_or_404(SupportTicket, pk=self.kwargs['ticket_id'])
        form.instance.ticket = ticket
        form.instance.user = self.request.user
        messages.success(self.request, 'Response added successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('ticket_detail', kwargs={'pk': self.kwargs['ticket_id']})

class FeedbackCreateView(LoginRequiredMixin, CreateView):
    model = Feedback
    form_class = FeedbackForm
    template_name = 'support/feedback_form.html'
    success_url = reverse_lazy('feedback_success')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Feedback submitted successfully.')
        return super().form_valid(form)

class FAQListView(ListView):
    model = FAQ
    template_name = 'support/faq_list.html'
    context_object_name = 'faqs'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        category = self.request.GET.get('category')
        if search:
            queryset = queryset.filter(Q(question__icontains=search) | Q(answer__icontains=search))
        if category:
            queryset = queryset.filter(category__id=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = FAQSearchForm(self.request.GET)
        context['categories'] = SupportCategory.objects.all()
        return context

class FAQCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = FAQ
    form_class = FAQForm
    template_name = 'support/faq_create.html'
    success_url = reverse_lazy('faq_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'FAQ created successfully.')
        return super().form_valid(form)

class SupportDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = SupportTicket
    template_name = 'support/dashboard.html'
    context_object_name = 'tickets'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['open_tickets'] = SupportTicket.objects.filter(status='OPEN').count()
        context['in_progress_tickets'] = SupportTicket.objects.filter(status='IN_PROGRESS').count()
        context['resolved_tickets'] = SupportTicket.objects.filter(status='RESOLVED').count()
        context['urgent_tickets'] = SupportTicket.objects.filter(priority='URGENT', status__in=['OPEN', 'IN_PROGRESS']).count()
        return context

class SupportCategoryListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = SupportCategory
    template_name = 'support/category_list.html'
    context_object_name = 'categories'

    def test_func(self):
        return self.request.user.is_staff

class SupportCategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = SupportCategory
    form_class = SupportCategoryForm
    template_name = 'support/category_create.html'
    success_url = reverse_lazy('category_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Category created successfully.')
        return super().form_valid(form)

def feedback_success(request):
    return render(request, 'support/feedback_success.html')

# Additional utility views

def search_view(request):
    query = request.GET.get('q')
    tickets = SupportTicket.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query)
    ) if query else SupportTicket.objects.none()
    
    faqs = FAQ.objects.filter(
        Q(question__icontains=query) | Q(answer__icontains=query)
    ) if query else FAQ.objects.none()

    context = {
        'tickets': tickets,
        'faqs': faqs,
        'query': query
    }
    return render(request, 'support/search_results.html', context)

class UserProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'support/user_profile.html'
    context_object_name = 'user_profile'

    def get_object(self):
        return self.request.user

class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'email']
    template_name = 'support/user_profile_update.html'
    success_url = reverse_lazy('user_profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)