from django.utils import timezone
from django.conf import settings
from datetime import datetime

class SessionRefreshMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            current_time = timezone.now()
            last_activity_str = request.session.get('last_activity')
            
            if last_activity_str:
                last_activity = datetime.fromisoformat(last_activity_str)
                time_passed = (current_time - last_activity).total_seconds()
                if time_passed < settings.SESSION_EXPIRE_SECONDS:
                    request.session['last_activity'] = current_time.isoformat()
            else:
                request.session['last_activity'] = current_time.isoformat()

        response = self.get_response(request)
        return response