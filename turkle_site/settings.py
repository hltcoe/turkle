# -*- coding: utf-8 -*-
# Django settings for turkle project.

import os

DEBUG = False
ALLOWED_HOSTS = ['*']

TURKLE_SITE_NAME = 'Turkle'

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

if 'TURKLE_DB_ENGINE' in os.environ and os.environ['TURKLE_DB_ENGINE'].lower() == 'mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ['TURKLE_DB_NAME'],
            'USER': os.environ['TURKLE_DB_USER'],
            'PASSWORD': os.environ['TURKLE_DB_PASSWORD'],
            'HOST': os.environ['TURKLE_DB_HOST'],
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite3',
        }
    }

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'imdcm3*5i8lov-m=0qu9-yxjuk!_qk$ykgde&amp;cxq(8n(l_a63*'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'turkle.utils.site',
            ],
        },
    },
]

MIDDLEWARE = (
    # Uncomment to use whitenoise to serve static files
    # 'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'turkle_site.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'turkle_site.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Our app comes before django.contrib.admin so that Django uses
    # our password change/reset templates instead of the templates
    # from django.contrib.admin
    'turkle',
    'django.contrib.admin',

    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'django_nose',
    'guardian',
    'dbbackup'
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # default
    'guardian.backends.ObjectPermissionBackend',
)


# Below is a possible logging configuration that sends HTTP 500
# errors to people lists in ADMINS and records an access log to
# logs/turkle.log. You will need to create the logs directory in
# the base of this repository (at the same level as examples).
# More options can be found in Django's logging docs:
# https://docs.djangoproject.com/en/1.11/topics/logging/
# ADMINS =(('name','email'),)
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'filters': {
#         'require_debug_false': {
#             '()': 'django.utils.log.RequireDebugFalse'
#         }
#     },
#     'handlers': {
#         'file': {
#             'level': 'INFO',
#             'class': 'logging.FileHandler',
#             'filename': os.path.join(os.path.dirname(__file__), os.pardir, 'logs', 'turkle.log'),
#         },
#         'mail_admins': {
#             'level': 'ERROR',
#             'filters': ['require_debug_false'],
#             'class': 'django.utils.log.AdminEmailHandler'
#         }
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['file'],
#             'level': 'INFO',
#             'propagate': True,
#         },
#         'django.request': {
#             'handlers': ['mail_admins'],
#             'level': 'ERROR',
#             'propagate': False,
#         },
#     }
# }

# Set max size for file uploads and POST requests to 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600

LOGIN_REDIRECT_URL = '/'

# If True, the "Password Reset" link will be added to the login form.
# This requires MTA configuration below.
TURKLE_EMAIL_ENABLED = False

# Configure connection to Mail Transfer Agent (MTA)
# more details at https://docs.djangoproject.com/en/1.11/ref/settings/#std:setting-EMAIL_HOST
# EMAIL_HOST = ''
# set the [from] email address
# DEFAULT_FROM_EMAIL = ''
# configure if not using the standard SMTP port 25
# EMAIL_PORT = 25
# uncomment if using secure connection to MTA
# EMAIL_USE_TLS = True
# configure if authenticating to MTA
# EMAIL_HOST_USER = ''
# EMAIL_HOST_PASSWORD = ''

# Uncomment and configure (Note: this does not work for sqlite databases)
# DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
# DBBACKUP_STORAGE_OPTIONS = {'location': '/opt/backups'}
