from django.conf import settings

from . import __version__


def get_site_name():
    try:
        return settings.TURKLE_SITE_NAME
    except AttributeError:
        pass
    return 'Turkle'


def get_turkle_template_limit(in_bytes=False):
    try:
        template_size_limit = settings.TURKLE_TEMPLATE_LIMIT
    except AttributeError:
        template_size_limit = 64
    if in_bytes:
        template_size_limit *= 1024
    return template_size_limit


def turkle_vars(request):
    """add variables to the template context"""
    return {
        'turkle_site_name': get_site_name(),
        'turkle_template_limit': get_turkle_template_limit(),
        'turkle_version': __version__,
    }
