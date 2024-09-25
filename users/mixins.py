from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)

class AdministratorRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and is an administrator."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            logger.warning(f"Unauthenticated user attempted to access {self.__class__.__name__}")
            return self.handle_no_permission()
        
        if not request.user.groups.filter(name='administrator').exists():
            logger.warning(f"User {request.user.username} attempted to access {self.__class__.__name__} without administrator privileges")
            raise PermissionDenied("You do not have administrator privileges.")
        
        return super().dispatch(request, *args, **kwargs)
    