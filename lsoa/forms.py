from collections import defaultdict

from django import forms
from django.urls import reverse_lazy
from related_select.fields import RelatedChoiceField

from lsoa.models import Course, LearningConstructSublevel


class ConstructModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def __init__(self, queryset, **kwargs):
        super(ConstructModelMultipleChoiceField, self).__init__(queryset, **kwargs)
        self.queryset = queryset.select_related()
        self.to_field_name = None

        self.choices = []
        _choices = defaultdict(list)

        for construct_sublevel in queryset:
            group = construct_sublevel.level.construct
            _choices[group.abbreviation].append((construct_sublevel.id, self.label_from_instance(construct_sublevel)))

        try:
            self.choices = [(cat_name, data) for cat_name, data in _choices.items()]
        except:
            pass

    def label_from_instance(self, obj):
        return '{} - {}'.format(obj.name, obj.description[:60])


class SetupForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.all())
    grouping = RelatedChoiceField(related_dependent='course', related_url=reverse_lazy('student-groupings-ajax'),
                                  empty_label='Individuals', required=False)
    constructs = ConstructModelMultipleChoiceField(queryset=LearningConstructSublevel.objects.all())

    def __init__(self, **kwargs):
        super(SetupForm, self).__init__(**kwargs)
        if self.is_bound:
            self.fields['grouping'].init_bound_field(self.data.get('course'))


class ObservationForm(forms.Form):
    pass
