from django.conf import settings
from django import template

register = template.Library()


@register.filter
def keyvalue(dict, key):
    return dict.get(key)


@register.filter
def selected_constructs(tables, filtered):
    if not filtered:
        return []
    filtered_ids = set(filtered.values_list('id', flat=True))
    return [table for table in tables if any(id in table['construct_map'] for id in filtered_ids)]


@register.filter
def selected_subconstructs(constructs, filtered):
    if not filtered:
        return []
    filtered_ids = set(filtered.values_list('id', flat=True))
    return [(id, construct) for id, construct in constructs if id in filtered_ids]
