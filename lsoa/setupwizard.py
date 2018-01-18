from urllib.parse import urlencode

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import Select
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from formtools.wizard.views import SessionWizardView

from utils.pagelets import PageletMixin
from .models import Course, StudentGrouping, LearningConstructSublevel


class DumbSelect(Select):
    def use_required_attribute(self, initial):
        return False


class ChooseCourseForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.all(), widget=DumbSelect())


class ChooseGroupsForm(forms.Form):
    grouping = forms.ModelChoiceField(queryset=StudentGrouping.objects.all(), required=False, widget=DumbSelect(),
                                      empty_label='Individual')

class CustomModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return '{} - {}'.format(obj.name, obj.description[:60])

class ChooseLearningConstructSublevelsForm(forms.Form):
    constructs = CustomModelMultipleChoiceField(queryset=LearningConstructSublevel.objects.all(),)


class SetupWizard(LoginRequiredMixin, PageletMixin, SessionWizardView):
    pagelet_name = 'pagelet_setup.html'
    form_list = [ChooseCourseForm, ChooseGroupsForm, ChooseLearningConstructSublevelsForm]

    def done(self, form_list, **kwargs):
        d = {}
        for form in form_list:
            d.update(form.cleaned_data)
        grouping = d['grouping']
        course = d['course']
        constructs = d['constructs']
        params = {
            'course': course.id,
            'constructs': [c.id for c in constructs]
        }
        if grouping:
            params['grouping'] = grouping.id
        return HttpResponseRedirect(reverse_lazy('observation_view') + '?' + urlencode(params, doseq=True))
