from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def meta_tag(tag):
    attributes = [f"{key}=\"{value}\"" for key, value in tag.items()]
    return mark_safe(f"<meta {' '.join(attributes)}>")
