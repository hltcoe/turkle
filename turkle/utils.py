from django.conf import settings


def get_site_name():
    try:
        return settings.TURKLE_SITE_NAME
    except AttributeError:
        pass
    return 'Turkle'


def site(request):
    """template context processor that adds turkle_site_name variable"""
    return {'turkle_site_name': get_site_name()}
