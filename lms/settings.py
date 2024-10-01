"""
Django settings for lms project.

Generated by 'django-admin startproject' using Django 5.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Custom apps
    'api',
    'users',
    'courses',
    'authentication',
    'website',
    'certificates',
    'quizzes',
    'leaderboard',
    'support',
    'announcements',
    'activities',
    'events',
    'organization',
    'gamification',
    'virtual_classroom',
    'maintenance',

    # Third-party apps
    'formtools',
    'corsheaders',
    'csp',
    'rosetta',
    'django_session_timeout',
    'crispy_forms',
    'crispy_tailwind',
    'widget_tweaks',
]

MIDDLEWARE = [
    'csp.middleware.CSPMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django_session_timeout.middleware.SessionTimeoutMiddleware',
    'users.middleware.SessionRefreshMiddleware',
    'maintenance.middleware.MaintenanceModeMiddleware',
]

ROOT_URLCONF = 'lms.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ BASE_DIR / 'templates' ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'users.context_processors.organization_logo',  
            ],
        },
    },
]

WSGI_APPLICATION = 'lms.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# Determine the environment
ENV = os.getenv('DJANGO_ENV', 'development')

# Database configuration
if ENV == 'production':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('en', _('English')),
    ('ar', _('Arabic')),
    ('fr', _('French')),
    ('de', _('German')),
    ('ja', _('Japanese')),
    ('hi', _('Hindi')),
    ('es', _('Spanish')),
    ('pt', _('Portuguese')),
    ('ru', _('Russian')),
    ('it', _('Italian')),
    ('ko', _('Korean')),
    ('nl', _('Dutch')),
    ('tr', _('Turkish')),
    ('pl', _('Polish')),
    ('sv', _('Swedish')),
    ('da', _('Danish')),
    ('fi', _('Finnish')),
    # ('no', _('Norwegian')),
    ('el', _('Greek')),
    ('he', _('Hebrew')),
    ('th', _('Thai')),
    ('vi', _('Vietnamese')),
    ('id', _('Indonesian')),
    ('bn', _('Bengali')),
    ('ta', _('Tamil')),
    ('te', _('Telugu')),
    ('kn', _('Kannada')),
    # ('gu', _('Gujarati')),
    ('pa', _('Punjabi')),
    ('mr', _('Marathi')),
    # ('or', _('Odia (Oriya)')),
    # ('kok', _('Konkani')),
    ('ml', _('Malayalam')),
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files (user-uploaded files)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = reverse_lazy('login')

# Custom user model
AUTH_USER_MODEL = 'users.User'

# SCORMHub API settings
SCORM_API_BASE_URL = os.getenv('SCORM_API_BASE_URL')
SCORM_API_TOKEN = os.getenv('SCORM_API_TOKEN')

# Logging settings
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}

# Allow embedding from all origins
X_FRAME_OPTIONS = 'ALLOWALL'

# Allow all origins for CORS
CORS_ALLOW_ALL_ORIGINS = True

# Remove CSP middleware if it's causing issues
MIDDLEWARE = [middleware for middleware in MIDDLEWARE if middleware != 'csp.middleware.CSPMiddleware']

# Email settings for Gmail
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# Session timeout settings
SESSION_EXPIRE_SECONDS = 18000
SESSION_EXPIRE_AFTER_LAST_ACTIVITY = True
SESSION_TIMEOUT_REDIRECT = 'session_expired'

MAINTENANCE_MODE = False
MAINTENANCE_BYPASS_QUERY_STRING = 'bypass_maintenance'