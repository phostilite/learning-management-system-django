# certificates/apps.py

from django.apps import AppConfig
import logging

class CertificatesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'certificates'

    def ready(self):
        import certificates.signals
        logging.info("Certificates app is ready and signals are connected")