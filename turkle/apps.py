from django.apps import AppConfig
from .utils import get_site_name


class TurkleAppConfig(AppConfig):
    name = 'turkle'
    verbose_name = get_site_name()
