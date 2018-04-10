from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView
from related_select.views import RelatedSelectView

from lsoa.forms import ObservationForm, SetupForm
from lsoa.models import Course, StudentGrouping, LearningConstructSublevel
from utils.pagelets import PageletMixin


class SetupView(LoginRequiredMixin, PageletMixin, FormView):
    pagelet_name = 'pagelet_setup.html'
    form_class = SetupForm

    def get_initial(self):
        initial = super(SetupView, self).get_initial()
        initial.update({
            'course': self.request.session.get('course'),
            'grouping': self.request.session.get('grouping'),
            'request': self.request
        })
        return initial

    def form_valid(self, form):
        d = form.cleaned_data
        grouping = d['grouping']
        course = d['course']
        constructs = d['constructs']
        params = {
            'course': course.id,
            'constructs': [c.id for c in constructs]
        }
        if grouping:
            params['grouping'] = grouping
        self.request.session['course'] = course.id
        self.request.session['grouping'] = grouping
        return HttpResponseRedirect(reverse_lazy('observation_view') + '?' + urlencode(params, doseq=True))

    def form_invalid(self, form):
        print(form.errors)
        return super(SetupView, self).form_invalid(form)


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
        kwargs['constructs'] = LearningConstructSublevel.objects.filter(pk__in=self.request.GET.getlist('constructs')) \
            .select_related('level', 'level__construct').prefetch_related('examples')
        return super().get_context_data(**kwargs)


class GroupingRelatedSelectView(RelatedSelectView):
    @staticmethod
    def filter(value, **kwargs):
        return StudentGrouping.objects.filter(course_id=value)

    def dispatch(self, request, *args, **kwargs):
        if request.method != 'GET':
            raise NotImplementedError('This view only accepts GET requests')
        v = request.GET.get('value', None)
        ajax_list = []
        for model_instance in self.filter(v, user=request.user):
            ajax_list.append({'key': self.to_text(model_instance),
                              'value': self.to_value(model_instance)})
        return JsonResponse(ajax_list, safe=False)
