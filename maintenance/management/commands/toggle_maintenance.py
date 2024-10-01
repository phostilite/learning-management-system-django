from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Toggles maintenance mode on or off'

    def handle(self, *args, **options):
        current_state = getattr(settings, 'MAINTENANCE_MODE', False)
        new_state = not current_state
        
        # Update the setting in memory
        settings.MAINTENANCE_MODE = new_state
        
        # Update the setting in the settings file
        settings_file = os.path.join(settings.BASE_DIR, 'lms', 'settings.py')
        with open(settings_file, 'r+') as f:
            content = f.read()
            content = content.replace(f"MAINTENANCE_MODE = {current_state}", f"MAINTENANCE_MODE = {new_state}")
            f.seek(0)
            f.write(content)
            f.truncate()

        self.stdout.write(self.style.SUCCESS(f'Maintenance mode is now {"ON" if new_state else "OFF"}'))