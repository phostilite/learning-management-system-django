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

    # Third-party apps
    'formtools',
    'corsheaders',
    'csp',
    'rosetta',
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
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
            ],
        },
    },
]

WSGI_APPLICATION = 'lms.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

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

# Custom user model
AUTH_USER_MODEL = 'users.User'

# CloudSCORM API settings
CLOUDSCORM_APP_ID = os.getenv('CLOUDSCORM_APP_ID')
CLOUDSCORM_SECRET_KEY = os.getenv('CLOUDSCORM_SECRET_KEY')
CLOUDSCORM_API_URL = os.getenv('CLOUDSCORM_API_URL')

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