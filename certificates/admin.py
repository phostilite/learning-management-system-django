# certificates/admin.py

from django.contrib import admin
from .models import Certificate, CertificateTemplate, CertificateIssuanceLog

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_number', 'learner', 'course', 'issue_date', 'is_valid')
    search_fields = ('certificate_number', 'learner__user__username', 'course__title')
    list_filter = ('is_valid', 'course', 'course_delivery')
    
    actions = ['revoke_certificates']

    def revoke_certificates(self, request, queryset):
        for certificate in queryset:
            certificate.revoke(revoked_by=request.user, reason="Administrative action")
        self.message_user(request, f"{queryset.count()} certificates have been revoked.")
    revoke_certificates.short_description = "Revoke selected certificates"

@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_default', 'created_at')
    list_filter = ('is_default',)
    actions = ['set_as_default']

    def set_as_default(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "You can only set one template as default at a time.", level='ERROR')
        else:
            queryset.update(is_default=True)
            self.message_user(request, "The selected template has been set as default.")
    set_as_default.short_description = "Set as default template"

@admin.register(CertificateIssuanceLog)
class CertificateIssuanceLogAdmin(admin.ModelAdmin):
    list_display = ('certificate', 'issued_by', 'issued_at', 'ip_address')
    search_fields = ('certificate__certificate_number', 'issued_by__username')
    list_filter = ('issued_at',)