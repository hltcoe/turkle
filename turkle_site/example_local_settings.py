# You can customize the site name displayed in the page title and
# navigation UI.
# TURKLE_SITE_NAME = 'Turkle'


# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
# STATIC_ROOT = ''


# Sample database settings for MySQL
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'turkle',
#         'USER': 'turkleuser',
#         'PASSWORD': 'password',
#         'HOST': 'localhost'
#     }
# }

# Sample database settings for Postgres
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'turkle',
#         'USER': 'turkleuser',
#         'PASSWORD': 'password',
#         'HOST': 'localhost'
#     }
# }


# Uncomment to use whitenoise to serve static files
# MIDDLEWARE = (
#     'whitenoise.middleware.WhiteNoiseMiddleware',
# ) + MIDDLEWARE


# If TURKLE_EMAIL_ENABLED is  True, the "Password Reset" link
# will be added to the login form.  This requires MTA configuration
# below.
# TURKLE_EMAIL_ENABLED = True

# Configure connection to Mail Transfer Agent (MTA)
# more details at https://docs.djangoproject.com/en/2.2/ref/settings/#std:setting-EMAIL_HOST
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
#     'formatters': {
#         'simple': {
#             'format': '%(asctime)s %(levelname)s: %(message)s',
#             'datefmt': '%Y-%m-%d %H:%M:%S',
#         },
#     },
#     'handlers': {
#         'file': {
#             'level': 'INFO',
#             'class': 'logging.FileHandler',
#             'filename': os.path.join(os.path.dirname(__file__), os.pardir, 'logs', 'turkle.log'),
#             'formatter': 'simple',
#         },
#         'mail_admins': {
#             'level': 'ERROR',
#             'class': 'django.utils.log.AdminEmailHandler'
#             'filters': ['require_debug_false'],
#         }
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['file'],
#             'level': 'WARNING',
#             'propagate': True,
#         },
#         'django.request': {
#             'handlers': ['mail_admins'],
#             'level': 'ERROR',
#             'propagate': False,
#         },
#         'turkle': {
#             'handlers': ['file'],
#             'level': 'INFO',
#             'propagate': True,
#         },
#     }
# }

# Example configuration for SAML authentication
SAML2_AUTH = {
    'DEFAULT_NEXT_URL': '/admin/',  # redirect url after login
    'CREATE_USER': True,  # create user if not already in the database
    'NEW_USER_PROFILE': {
        'USER_GROUPS': [],  # The default group name when a new user logs in
        'ACTIVE_STATUS': True,  # The default active status for new users
        'STAFF_STATUS': True,  # The staff status for new users
        'SUPERUSER_STATUS': False,  # The superuser status for new users
    },
    'ATTRIBUTES_MAP': {  # Change Email/UserName/FirstName/LastName to corresponding SAML2 userprofile attributes.
        'email': 'Email',
        'username': 'UserName',
        'first_name': 'FirstName',
        'last_name': 'LastName',
    },
    'TRIGGER': {
        'CREATE_USER': 'path.to.your.new.user.hook.method',
        'BEFORE_LOGIN': 'path.to.your.login.hook.method',
    },
    'ASSERTION_URL': 'https://your-domain.com',  # Custom URL to validate incoming SAML requests against
    'ENTITY_ID': 'https://your-domain.com/saml2_auth/acs/',  # Populates the Issuer element in authn request
    'NAME_ID_FORMAT': 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress',
    'USE_JWT': False,  # Set this to True if you are running a Single Page Application (SPA) with Django Rest Framework (DRF)
    'FRONTEND_URL': 'http://localhost:8000',  # URL of the SPA if you are using one
    'JWT_EXP': 3600,  # JWT expiration time in seconds
}
