
# Standard

# Third Party
from django import template
from inflection import titleize

# Local


register = template.Library()


@register.filter(name="verbose_name")
def verbose_name(value):
    return titleize(value.__class__.__name__)
