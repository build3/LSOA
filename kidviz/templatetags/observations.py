from django.conf import settings
from django import template

register = template.Library()


@register.filter
def contains(observations, construct):
    return any(o.level.construct == construct for o in observations)


@register.filter
def observation_pks(observations):
    return [o.pk for o in observations]
