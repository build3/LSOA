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


@register.simple_tag(takes_context=True)
def get_color_star_chart_4(context, sublevel, level_observations, construct):
    all_observations = 0

    for sublevel, observations in context['star_chart_4'][construct].items():
        all_observations += len(observations)

    return sublevel.get_color_dark(len(level_observations), all_observations)
