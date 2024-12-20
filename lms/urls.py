"""
URL configuration for lms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language
from django.utils.translation import gettext_lazy as _

urlpatterns = [
    # Include API URLs outside i18n_patterns
    path('api/', include('api.urls', namespace='api')),
]

# Add other URL patterns that should have language prefix
urlpatterns += i18n_patterns(
    path('i18n/setlang/', set_language, name='set_language'),
    path('admin/', admin.site.urls),
    path('auth/', include('authentication.urls')),
    path('user/', include('users.urls')),
    path('', include('website.urls')),
    path('rosetta/', include('rosetta.urls')),
    path('certificates/', include('certificates.urls')),
    path(_('quizzes/'), include('quizzes.urls')),
    path('organization/', include('organization.urls')),
    prefix_default_language=True
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

