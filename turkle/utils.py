from django.conf import settings

from . import __version__


def get_site_name():
    return getattr(settings, 'TURKLE_SITE_NAME', 'Turkle')


def get_turkle_template_limit(in_bytes=False):
    """get template size limit in kb by default"""
    template_size_limit = getattr(settings, 'TURKLE_TEMPLATE_LIMIT', 64)
    if in_bytes:
        template_size_limit *= 1024
    return template_size_limit


def turkle_vars(request):
    """add variables to the template context"""
    return {
        'turkle_site_name': get_site_name(),
        'turkle_template_limit': get_turkle_template_limit(),
        'turkle_version': __version__,
        'turkle_email_enabled': getattr(settings, 'TURKLE_EMAIL_ENABLED', False),
        'turkle_meta_tags': getattr(settings, 'META_TAGS', []),
    }


def are_anonymous_tasks_allowed():
    return getattr(settings, 'TURKLE_ANONYMOUS_TASKS', True)
