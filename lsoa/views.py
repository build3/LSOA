from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import FormView

from lsoa.forms import ObservationForm
from lsoa.models import Course, StudentGrouping, LearningConstructSublevel
from utils.pagelets import PageletMixin


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
        kwargs['constructs'] = LearningConstructSublevel.objects.filter(pk__in=self.request.GET.getlist('constructs'))\
            .select_related('level', 'level__construct').prefetch_related('examples')
        return super().get_context_data(**kwargs)
