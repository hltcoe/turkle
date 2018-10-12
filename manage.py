#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "turkle_site.settings")

    from django.core.management import execute_from_command_line

    # Allow Django to serve static files even if the DEBUG setting is False.
    # This behavior is only enabled if Django is run using:
    #   python manage.py runserver
    # If Django is started as a WSGI process, it will not serve static files.
    #
    # Official warning from documentation about the --insecure flag:
    #
    #   Use the --insecure option to force serving of static files
    #   with the staticfiles app even if the DEBUG setting is
    #   False. By using this you acknowledge the fact that it's
    #   grossly inefficient and probably insecure. This is only
    #   intended for local development, should never be used in
    #   production and is only available if the staticfiles app is in
    #   your project's INSTALLED_APPS setting. runserver --insecure
    #   doesn't work with CachedStaticFilesStorage.
    #     https://docs.djangoproject.com/en/1.11/ref/contrib/staticfiles/#runserver
    if 'runserver' in sys.argv:
        sys.argv.append('--insecure')

    execute_from_command_line(sys.argv)
