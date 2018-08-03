from collections import defaultdict

from django import forms
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from django.forms.widgets import SelectMultiple
from django.urls import reverse_lazy
from threadlocals.threadlocals import get_current_request
from related_select.fields import RelatedChoiceField

from lsoa.fields import RelatedChoiceFieldWithAfter
from lsoa.models import Course, LearningConstructSublevel, ContextTag, Observation


class TagWidget(SelectMultiple):
    input_type = 'tag'


class TagField(forms.ModelMultipleChoiceField):
    widget = TagWidget

    def label_from_instance(self, obj):
        return obj.text

    def clean(self, value):
        assert type(value) == list
        tags = []
        request = get_current_request()

        for tag_text in value:
            if type(tag_text) == str:
                try:
                    tags.append(ContextTag.objects.get(id=tag_text, owner=request.user))
                except Exception:
                    ct = ContextTag(text=tag_text, owner=request.user)
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
    grouping = RelatedChoiceField(
        related_dependent='course',
        related_url=reverse_lazy('student-groupings-ajax'),
        empty_label='Individuals',
        required=False)
    constructs = ConstructModelMultipleChoiceField(queryset=LearningConstructSublevel.objects.all(),
                                                   widget=forms.CheckboxSelectMultiple)
    context_tags = TagField(queryset=ContextTag.objects.all(), required=False)

    def __init__(self, **kwargs):
        super(SetupForm, self).__init__(**kwargs)
        if self.is_bound and self.data.get('course'):
            self.fields['grouping'].init_bound_field(self.data.get('course'))

        request = get_current_request()
        self.fields['context_tags'].queryset = ContextTag.objects.filter(owner=request.user)

        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class ObservationForm(forms.ModelForm):
    """
    An Observation is a "snapshot in time" of student(s) exhibiting mastery of
    a certain (or multiple) learning constructs, paired with typed notes or
    visual evidence (picture or video).
    """

    class Meta:
        model = Observation
        fields = ['students', 'constructs', 'tags', 'annotation_data', 'original_image', 'video',
                  'notes', 'video_notes', 'parent', 'owner', 'name', 'course', 'grouping', 'construct_choices', ]
        widgets = {
            'course': forms.HiddenInput(),
            'grouping': forms.HiddenInput(),
            'owner': forms.HiddenInput(),
            'name': forms.HiddenInput(),
            'construct_choices': forms.HiddenInput(),
            'tags': forms.MultipleHiddenInput(),
            'notes': forms.Textarea(attrs={'class': 'notes-container'}),
        }

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=None,
                 empty_permitted=False, instance=None, use_required_attribute=None):
        if data:
            data = data.copy()
            if not data.get('useMostRecentMedia'):
                data['parent'] = None

        super().__init__(data=data, files=files, auto_id=auto_id, prefix=prefix,
                         initial=initial, error_class=error_class, label_suffix=label_suffix,
                         empty_permitted=empty_permitted, instance=instance,
                         use_required_attribute=use_required_attribute)

    def clean(self):
        super().clean()
        if self.cleaned_data.get('annotation_data') or self.cleaned_data['original_image']:
            if self.cleaned_data['video']:
                self.add_error(field=None, error='Technical Error: Video was uploaded alongside an image. Something\'s wrong')

        if not self.cleaned_data['students']:
            self.add_error(field='students', error='You must choose at least one student for the observation')

        if not self.cleaned_data['constructs']:
            self.add_error(field='constructs', error='You must choose at least one learning construct for the observation')

        return self.cleaned_data


class GroupingForm(forms.Form):
    pass


class NewCourseForm(forms.Form):
    course_name = forms.CharField()
    student_csv = forms.FileField()

    def clean_student_csv(self):
        pass

class ContextTagForm(forms.ModelForm):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    class Meta:
        model = ContextTag
        fields = ['text', 'color']
