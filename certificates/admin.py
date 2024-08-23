from django.contrib import admin

from .models import Certificate, CertificateTemplate, CertificateIssuanceLog

admin.site.register(Certificate)
admin.site.register(CertificateTemplate)
admin.site.register(CertificateIssuanceLog)
