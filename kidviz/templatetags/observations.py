from django import template

from ..models import Course

register = template.Library()


@register.filter
def contains(observations, construct):
    return any(o.level.construct == construct for o in observations)


@register.filter
def observation_pks(observations):
    return [o.pk for o in observations]


@register.filter
def course_from_session_or_first(request):
    return request.session.get('course') or Course.objects.order_by('id').first().pk


@register.filter
def get_color_for_sublevel(obj, observations):
    return obj.get_color(len(observations))
