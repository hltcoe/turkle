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
    meta_tags = settings.META_TAGS if hasattr(settings, 'META_TAGS') else []

    return {
        'turkle_site_name': get_site_name(),
        'turkle_template_limit': get_turkle_template_limit(),
        'turkle_version': __version__,
        'turkle_email_enabled': settings.TURKLE_EMAIL_ENABLED,
        'turkle_meta_tags': meta_tags,
    }
