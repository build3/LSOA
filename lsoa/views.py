from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView

from lsoa.forms import ObservationForm, ObservationSetupForm
from lsoa.models import StudentGrouping, Course
from utils.pagelets import PageletMixin


class ObservationSetupView(LoginRequiredMixin, PageletMixin, FormView):
    pagelet_name = 'pagelet_setup.html'
    form_class = ObservationSetupForm

    def form_valid(self, form):
        self.form = form
        return super().form_valid(form)

    def get_success_url(self):
        grouping = self.form.cleaned_data['grouping']
        course = self.form.cleaned_data['course']
        params = {
            'course': course.id
        }
        if grouping:
            params['grouping'] = grouping.id
        return reverse_lazy('observation_view') + '?' + urlencode(params, doseq=True)


class ObservationView(LoginRequiredMixin, PageletMixin, FormView):
    pagelet_name = 'pagelet_observation.html'
    form_class = ObservationForm

    def get(self, request, *args, **kwargs):
        if not self.request.GET.get('course'):
            return HttpResponseRedirect(reverse('observation_setup_view'))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        if self.request.GET.get('grouping'):
            kwargs['grouping'] = StudentGrouping.objects.filter(pk=self.request.GET.get('grouping')).first()
        kwargs['course'] = Course.objects.filter(pk=self.request.GET.get('course')).first()
        return super().get_context_data(**kwargs)
