# support/admin.py
from django.contrib import admin
from .models import SupportCategory, SupportTicket, TicketResponse, FAQ, Feedback

admin.site.register(SupportCategory)
admin.site.register(SupportTicket)
admin.site.register(TicketResponse)
admin.site.register(FAQ)
admin.site.register(Feedback)