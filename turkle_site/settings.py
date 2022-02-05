# -*- coding: utf-8 -*-
# Django settings for turkle project.

import os
import sys
import types

DEBUG = False
ALLOWED_HOSTS = ['*']
X_FRAME_OPTIONS = 'SAMEORIGIN'

TURKLE_SITE_NAME = 'Turkle'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

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
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'turkle.utils.turkle_vars',
            ],
        },
    },
]

MIDDLEWARE = (
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
    'guardian',
    'admin_auto_filters',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # default
    'guardian.backends.ObjectPermissionBackend',
)


# Set max size for file uploads and POST requests to 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600

# max size of template in KB
TURKLE_TEMPLATE_LIMIT = 64

LOGIN_REDIRECT_URL = 'index'

# If True, the "Password Reset" link will be added to the login form.
# This requires MTA configuration.
TURKLE_EMAIL_ENABLED = False


# Docker specific configuration

# Running with a URL prefix ("sub-directory").
# Configure your reverse proxy appropriately.
# Set the environment variable 'TURKLE_PREFIX' to the URL prefix
# Warning: this could break templates that depend on using Turkle JS or CSS files.
# Note: this is intended for the Docker image runtime configuration
if 'TURKLE_PREFIX' in os.environ:
    FORCE_SCRIPT_NAME = os.environ['TURKLE_PREFIX']
    if FORCE_SCRIPT_NAME[0] != '/':
        FORCE_SCRIPT_NAME = '/' + FORCE_SCRIPT_NAME
    # If manually configuring location of static files, comment line below
    STATIC_URL = FORCE_SCRIPT_NAME + STATIC_URL

# override database configuration when running as under Docker with MySQL
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

if 'TURKLE_DOCKER' in os.environ:
    MIDDLEWARE = ('whitenoise.middleware.WhiteNoiseMiddleware', *MIDDLEWARE)
    STATIC_ROOT = os.path.join(os.getcwd(), 'staticfiles')
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '%(asctime)s %(levelname)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            }
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': True,
            },
            'turkle': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': True,
            },
        },
    }


##################
# LOCAL SETTINGS #
##################

# This implementation of local settings adapted from:
#   https://github.com/stephenmcd/mezzanine/blob/master/mezzanine/project_template/project_name/settings.py#L315

# Allow any settings to be defined in local_settings.py (which should be
# ignored in your version control system), allowing for settings to be
# defined per machine.

# Instead of doing "from .local_settings import *", we use exec so that
# local_settings has full access to everything defined in this module.
# Also force into sys.modules so it's visible to Django's autoreload.

# Full filesystem path to the project.
PROJECT_APP_PATH = os.path.dirname(os.path.abspath(__file__))
PROJECT_APP = os.path.basename(PROJECT_APP_PATH)

f = os.path.join(PROJECT_APP_PATH, "local_settings.py")
if os.path.exists(f):
    module_name = "%s.local_settings" % PROJECT_APP
    module = types.ModuleType(module_name)
    module.__file__ = f
    sys.modules[module_name] = module
    try:
        with open(f, "rb") as fh:
            exec(fh.read())
    except Exception as err:
        # Python traceback output lists problems in local_settings.py as
        # occurring in 'File "<string>"`, which may confuse users.
        if err.args[1][0] == '<string>':
            # Exception thrown directly from local_settings.py
            raise type(err)('%s on line %d of File "%s"' %
                            (err.args[0], err.args[1][1], f)) from err
        else:
            # Exception thrown from file used by local_settings.py
            raise err
