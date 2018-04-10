from collections import defaultdict

from django import forms
from django.forms import FileField, ValidationError
from django.urls import reverse_lazy
from django.forms.widgets import SelectMultiple
from related_select.fields import RelatedChoiceField

from lsoa.models import Course, LearningConstructSublevel, ContextTag


class TagWidget(SelectMultiple):
    input_type = 'tag'


class TagField(forms.ModelMultipleChoiceField):
    widget = TagWidget

    def label_from_instance(self, obj):
        return obj.text

    def clean(self, value, user):
        assert type(value) == list
        tags = []

        for tag_text in value:
            if type(tag_text) == str:
                try:
                    tags.append(ContextTag.objects.get(id=tag_text, owner=user))
                except Exception:
                    ct = ContextTag(text=tag_text, owner=user)
                    ct.save()
                    tags.append(ct)
        return tags


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
    context_tags = TagField(queryset=ContextTag.objects.all(), required=False)

    def __init__(self, **kwargs):
        super(SetupForm, self).__init__(**kwargs)
        if self.is_bound:
            self.fields['grouping'].init_bound_field(self.data.get('course'))

        if self.initial['request']:
            self.user = self.initial['request'].user
            self.fields['context_tags'].queryset = ContextTag.objects.filter(owner=self.user)

    def _clean_fields(self):
        for name, field in self.fields.items():
            """Custom because we need to support TagField and pass in user"""
            if field.disabled:
                value = self.get_initial_for_field(field, name)
            else:
                value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))
            try:
                if isinstance(field, FileField):
                    initial = self.get_initial_for_field(field, name)
                    value = field.clean(value, initial)
                elif isinstance(field, TagField):
                    value = field.clean(value, self.user)
                else:
                    value = field.clean(value)
                self.cleaned_data[name] = value
                if hasattr(self, 'clean_%s' % name):
                    value = getattr(self, 'clean_%s' % name)()
                    self.cleaned_data[name] = value
            except ValidationError as e:
                self.add_error(name, e)


class ObservationForm(forms.Form):
    pass
