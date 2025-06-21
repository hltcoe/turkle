from django.conf import settings
from django.core.exceptions import ValidationError

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


def process_html_template(html_template):
    """Process the template as a string
       Returns: (has_submit, fields)
    """
    import re
    from bs4 import BeautifulSoup

    if len(html_template) > get_turkle_template_limit(True):
        raise ValidationError({'html_template': 'Template is too large'}, code='invalid')

    soup = BeautifulSoup(html_template, 'html.parser')
    has_submit_button = bool(soup.select('input[type=submit]'))

    # Extract fieldnames from html_template text, save fieldnames as keys of a dict
    unique_fieldnames = set(re.findall(r'\${(\w+)}', html_template))
    fieldnames = dict((fn, True) for fn in unique_fieldnames)

    # Matching mTurk we confirm at least one input, select, or textarea
    if not (soup.find('input') or soup.find('select') or soup.find('textarea')):
        msg = (
            "Template does not contain any fields for responses. "
            "Please include at least one field (input, select, or textarea). "
            "This usually means you are generating HTML with JavaScript. "
            "If so, add an unused hidden input."
        )
        raise ValidationError({'html_template': msg}, code='invalid')

    return has_submit_button, fieldnames
