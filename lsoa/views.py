import json
from datetime import datetime, timedelta
from urllib.parse import urlencode

from braces.views import JSONResponseMixin
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, View
from related_select.views import RelatedSelectView

from lsoa.forms import ObservationForm, SetupForm, GroupingForm
from lsoa.models import Course, StudentGrouping, LearningConstructSublevel, LearningConstruct, StudentGroup, Student, \
    Observation
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
        tags = d['context_tags']
        params = {
            'course': course.id,
            'constructs': [c.id for c in constructs],
            'context_tags': [ct.id for ct in tags]
        }
        if grouping:
            params['grouping'] = grouping
        self.request.session['course'] = course.id
        self.request.session['grouping'] = grouping
        return HttpResponseRedirect(reverse_lazy('observation_view') + '?' + urlencode(params, doseq=True))

    def get_context_data(self, **kwargs):
        r = super(SetupView, self).get_context_data(**kwargs)
        r['form'].fields['grouping'].init_bound_field(r['form'].initial.get('course'))
        r['constructs'] = []
        for lc in LearningConstruct.objects.all():
            construct = {
                'name': lc.name,
                'levels': [],
            }
            for lcl in lc.learningconstructlevel_set.all():
                level = {
                    'name': '{}) {}'.format(lcl.level, lcl.description),
                    'sublevels': []
                }
                for lcsl in lcl.learningconstructsublevel_set.all():
                    sublevel = {
                        'id': lcsl.id,
                        'name': lcsl.name,
                        'description': lcsl.description
                    }
                    level['sublevels'].append(sublevel)
                construct['levels'].append(level)
            r['constructs'].append(construct)
        return r


class GroupingView(LoginRequiredMixin, PageletMixin, FormView):
    pagelet_name = 'pagelet_grouping.html'
    form_class = GroupingForm

    def get(self, request, *args, **kwargs):
        if not self.request.GET.get('course'):
            return HttpResponseRedirect(reverse('observation_setup_view'))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['course'] = Course.objects.filter(pk=self.request.GET.get('course')).prefetch_related('students').first()
        if self.request.GET.get('grouping'):
            kwargs['grouping'] = StudentGrouping.objects.get(id=self.request.GET.get('grouping'))
        else:
            kwargs['grouping'] = StudentGrouping(course=kwargs['course'])
        kwargs['initial_grouping_dict'] = {}
        if kwargs['grouping'].id:
            kwargs['initial_grouping_dict'] = {
                g.id: {'name': g.name, 'student_ids': [i for i in g.students.values_list('id', flat=True)]} for g in
                kwargs['grouping'].groups.all()}
        kwargs['initial_grouping_dict'] = json.dumps(kwargs['initial_grouping_dict'])
        return super().get_context_data(**kwargs)


class ObservationView(LoginRequiredMixin, PageletMixin, FormView):
    pagelet_name = 'pagelet_observation.html'
    form_class = ObservationForm
    success_url = reverse_lazy('observation_view')

    def get(self, request, *args, **kwargs):
        if not self.request.GET.get('course'):
            return HttpResponseRedirect(reverse('observation_setup_view'))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        if self.request.GET.get('grouping'):
            kwargs['grouping'] = StudentGrouping.objects.filter(pk=int(self.request.GET.get('grouping'))).first()
        kwargs['course'] = Course.objects.filter(pk=self.request.GET.get('course')).first()
        kwargs['constructs'] = LearningConstructSublevel.objects.filter(pk__in=self.request.GET.getlist('constructs')) \
            .select_related('level', 'level__construct').prefetch_related('examples')

        within_timeframe = datetime.now() - timedelta(hours=2)
        # TODO: Update this query to be correct.
        kwargs['most_recent_observation'] = Observation.objects \
            .filter(owner=self.request.user, created__gte=within_timeframe) \
            .order_by('-created').first()

        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Observation added')
        return super().form_valid(form)


class GroupingRelatedSelectView(RelatedSelectView):

    @staticmethod
    def blank_value():
        return '', 'Individuals'

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


@method_decorator(csrf_exempt, name='dispatch')
class GroupingSubmitView(LoginRequiredMixin, JSONResponseMixin, View):
    """
    To hell with writing a form view for this. Too complicated
    """

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        course_id = data.get('course_id', None) or None
        course = Course.objects.get(id=course_id)
        grouping_id = data.get('grouping_id', None) or None
        if grouping_id:
            grouping = StudentGrouping.objects.get(id=grouping_id)
        else:
            grouping = StudentGrouping()

        grouping.name = data.get('grouping_name', '')
        grouping.course = course
        grouping.save()
        grouping.groups.clear()

        for group_data in data.get('groupings'):
            group_id = group_data.get('id', None)
            if group_id:
                group = StudentGroup.objects.get(id=group_id)
            else:
                group = StudentGroup()
            group.name = group_data.get('name', '')
            group.course = course
            group.save()
            group.students.clear()

            for student_id in group_data.get('studentIds', []):
                student = Student.objects.get(id=student_id)
                group.students.add(student)

            grouping.groups.add(group)

        return_data = {
            'error': False,
            'messages': []
        }
        self.request.session['course'] = course.id
        self.request.session['grouping'] = grouping.id
        return self.render_json_response(return_data)
