from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def is_installed(app):
    return app in settings.INSTALLED_APPS


@register.filter
def meta_tag(tag):
    attributes = [f"{key}=\"{value}\"" for key, value in tag.items()]
    return mark_safe(f"<meta {' '.join(attributes)}>")


@register.filter()
def add_class(field, css):
    return field.as_widget(attrs={"class": css})
