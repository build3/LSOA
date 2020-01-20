from collections import defaultdict

from django import forms
from django.db.models import Q
from django.forms.utils import ErrorList
from django.forms.widgets import Select, SelectMultiple
from django.urls import reverse_lazy
from related_select.fields import RelatedChoiceField
from threadlocals.threadlocals import get_current_request

from kidviz.models import (Course, LearningConstruct, LearningConstructSublevel, ContextTag,
    Observation, Setup, Student)
from users.models import User


class TagWidget(SelectMultiple):
    input_type = 'tag'


class TagField(forms.ModelMultipleChoiceField):
    widget = TagWidget

    def label_from_instance(self, obj):
        return obj.text

    def clean(self, value):
        assert type(value) == list
        tags = []
        print(value)
        for tag_id in value:
            tag = ContextTag.objects.filter(id=tag_id).first()
            if tag:
                tags.append(tag)
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
    curricular_focus = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, **kwargs):
        super(SetupForm, self).__init__(**kwargs)
        if self.is_bound and self.data.get('course'):
            self.fields['grouping'].init_bound_field(self.data.get('course'))

        request = get_current_request()
        self.fields['context_tags'].queryset = ContextTag.objects.filter(Q(owner=request.user) | Q(owner__isnull=True))

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
        fields = [
            'students', 'constructs', 'tag_choices', 'tags', 'annotation_data',
            'original_image', 'video', 'observation_date', 'no_constructs',
            'notes', 'video_notes', 'parent', 'owner', 'name', 'course',
            'grouping', 'construct_choices', 'curricular_focus', 'is_draft', 'external_video', 'image_width'
        ]
        widgets = {
            'course': forms.HiddenInput(),
            'grouping': forms.HiddenInput(),
            'owner': forms.HiddenInput(),
            'name': forms.HiddenInput(),
            'construct_choices': forms.HiddenInput(),
            'tag_choices': forms.HiddenInput(),
            'notes': forms.Textarea(attrs={'class': 'notes-container'}),
            'observation_date': forms.DateInput(attrs={
                'class': 'datepicker form-control',
                'data-format': 'yyyy-mm-dd'
            }),
            'curricular_focus': forms.HiddenInput(),
            'video_notes': forms.ClearableFileInput(attrs={'accept': 'video/*'}),
            'video': forms.ClearableFileInput(attrs={'accept': 'video/*'}),
            'original_image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'external_video': forms.TextInput(attrs={'class': 'form-control'})
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
                self.add_error(field=None,
                               error='Technical Error: Video was uploaded alongside an image. Something\'s wrong')

        if not self.cleaned_data['students']:
            self.add_error(field='students', error='You must choose at least one student for the observation')

        if not (self.cleaned_data['constructs'] or self.cleaned_data['no_constructs']):
            self.add_error(field='constructs',
                           error='You must choose at least one learning construct for the observation')

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


class DateFilteringForm(forms.Form):
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'datepicker form-control'}),
        required=False
    )
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'datepicker form-control'}),
        required=False
    )
    tags = forms.ModelMultipleChoiceField(
        widget=forms.widgets.SelectMultiple(attrs={'class': 'form-control'}),
        required=False,
        queryset=ContextTag.objects.all()
    )
    constructs = forms.ModelMultipleChoiceField(
        widget=forms.widgets.SelectMultiple(attrs={'class': 'form-control'}),
        required=False,
        queryset=LearningConstructSublevel.objects.all()
    )
    courses = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Course.objects.all(),
        widget=forms.widgets.SelectMultiple(attrs={'class': 'form-control'})
    )
    learning_construct = forms.ChoiceField(
        widget=forms.widgets.Select(attrs={'class': 'form-control'}),
        required=False,
        choices=[]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        constructs = LearningConstruct.objects.all()

        choices = [('', '--------')]
        choices.extend([(construct.id, construct.name) for construct in constructs])
        choices.append((LearningConstruct.NO_CONSTRUCT, 'No construct'))

        self.fields['learning_construct'].choices = choices


class DraftObservationForm(ObservationForm):
    """This form is used to save draft observation without any validation."""
    
    def clean(self):
        """Remove validation from parent form."""
        return self.cleaned_data


class StudentFilterForm(forms.Form):
    students = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Student.objects.all(),
        widget=forms.widgets.SelectMultiple(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, queryset=None, **kwargs):
        super().__init__(*args, **kwargs)

        if queryset:
            self.fields['students'].queryset = queryset


class CourseFilterForm(forms.Form):
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        widget=forms.widgets.Select(attrs={'class': 'form-control'}),
        empty_label=None
    )


class SetupSaveForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.all(), required=False)

    class Meta:
        model = Setup
        fields = ('user', 'context_tags', 'grouping', 'course', 'constructs')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = get_current_request()
        self.fields['context_tags'].queryset = ContextTag.objects.filter(
            Q(owner=request.user)
            | Q(owner__isnull=True)
        )
