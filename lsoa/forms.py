from django import forms

from lsoa.models import StudentGrouping, Course


class ObservationSetupForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.all())
    grouping = forms.ModelChoiceField(queryset=StudentGrouping.objects.all(), required=False)

class ObservationForm(forms.Form):
    pass
