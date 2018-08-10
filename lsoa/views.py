import io
import logging

import collections
import json

from datetime import timedelta
from braces.views import JSONResponseMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, View, TemplateView, UpdateView, \
    CreateView, ListView
from related_select.views import RelatedSelectView
from tablib import Dataset

from lsoa.exceptions import InvalidFileFormatError
from lsoa.forms import ObservationForm, SetupForm, GroupingForm, ContextTagForm, \
    DateFilteringForm
from lsoa.models import (
    ContextTag, Course, StudentGrouping, LearningConstructSublevel,
    LearningConstruct, StudentGroup, Student, Observation
)
from lsoa.resources import ClassRoster, ACCEPTED_FILE_EXTENSIONS

logger = logging.getLogger(__name__)


class SetupView(LoginRequiredMixin, FormView):
    template_name = 'setup.html'
    form_class = SetupForm

    def get_initial(self):
        initial = super(SetupView, self).get_initial()
        initial.update({
            'course': self.request.session.get('course'),
            'grouping': self.request.session.get('grouping'),
            'constructs': self.request.session.get('constructs'),
            'context_tags': self.request.session.get('context_tags'),
            'request': self.request
        })
        return initial

    def form_valid(self, form):
        d = form.cleaned_data
        grouping = d['grouping']
        course = d['course']
        constructs = d['constructs']
        tags = d['context_tags']
        self.request.session['course'] = course.id
        self.request.session['grouping'] = grouping
        self.request.session['constructs'] = [c.id for c in constructs]
        self.request.session['context_tags'] = [t.id for t in tags]
        return HttpResponseRedirect(reverse_lazy('observation_view'))

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
                    'id': lcl.id,
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


class GroupingView(LoginRequiredMixin, FormView):
    template_name = 'grouping.html'
    form_class = GroupingForm

    def get(self, request, *args, **kwargs):
        if not self.request.GET.get('course'):
            return HttpResponseRedirect(reverse('setup'))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['course'] = Course.objects.filter(pk=self.request.GET.get('course')).prefetch_related(
            'students').first()
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


class ObservationCreateView(SuccessMessageMixin, LoginRequiredMixin, FormView):
    template_name = 'observation.html'
    form_class = ObservationForm
    success_message = 'Observation Added'

    def get_success_url(self):
        return reverse_lazy('observation_view')

    def get(self, request, *args, **kwargs):
        if not self.request.session.get('course'):
            return HttpResponseRedirect(reverse('setup'))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if self.request.POST.get('use_recent_observation'):
            kwargs['use_recent_observation'] = True
            recent_observation = get_recent_observations(self.request.user).first()
            if recent_observation:
                self.initial['original_image'] = recent_observation.original_image
                self.initial['video'] = recent_observation.video
            return self.get(request, *args, **kwargs)
        else:
            return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        session_course = self.request.session.get('course')
        session_grouping = self.request.session.get('grouping')
        session_construct_choices = self.request.session.get('constructs') or []
        session_tags = self.request.session.get('context_tags') or []
        last_observation_id = self.request.session.get('last_observation_id')

        course = Course.objects.filter(pk=session_course).first()
        grouping = None
        if session_grouping:
            grouping = StudentGrouping.objects.filter(pk=session_grouping).first()

        self.initial.update({
            'name': '{} Observed'.format(course.name),
            'course': course, 'grouping': grouping, 'tag_choices': session_tags,
            'construct_choices': session_construct_choices, 'owner': self.request.user,
        })
        if last_observation_id:
            kwargs['last_observation_url'] = reverse_lazy('observation_detail_view', kwargs={'pk': last_observation_id})

        available_tags = ContextTag.objects.filter(pk__in=session_tags)

        if self.request.POST:
            chosen_tags = [int(item) for item in self.request.POST.getlist('tags')]
        else:
            # select all tags by default
            chosen_tags = [tag.id for tag in available_tags]

        kwargs['header'] = 'New Observation'
        kwargs['course'] = course
        kwargs['grouping'] = grouping
        kwargs['tags'] = available_tags
        kwargs['construct_choices'] = get_constructs(pk_list=session_construct_choices)
        kwargs['chosen_students'] = json.dumps([int(item) for item in self.request.POST.getlist('students')])
        kwargs['chosen_constructs'] = json.dumps([int(item) for item in self.request.POST.getlist('constructs')])
        kwargs['chosen_tags'] = chosen_tags
        kwargs['recent_observation'] = get_recent_observations(owner=self.request.user).first()

        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        obj = form.save()
        self.request.session['last_observation_id'] = obj.id
        return super().form_valid(form)


class ObservationDetailView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    model = Observation
    template_name = 'observation.html'
    form_class = ObservationForm
    success_message = 'Observation Updated'

    def get_success_url(self):
        return reverse_lazy('observation_detail_view', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):

        available_tags = self.object.tag_choices
        kwargs['header'] = self.object.name.strip() or 'Observation {}'.format(self.object.id)
        kwargs['created'] = self.object.created
        kwargs['course'] = self.object.course
        kwargs['grouping'] = self.object.grouping
        kwargs['tags'] = ContextTag.objects.filter(owner=self.request.user, pk__in=available_tags)
        kwargs['construct_choices'] = get_constructs(pk_list=self.object.construct_choices)
        kwargs['chosen_students'] = json.dumps(list(self.object.students.all().values_list('id', flat=True)))
        kwargs['chosen_constructs'] = json.dumps(list(self.object.constructs.all().values_list('id', flat=True)))
        kwargs['chosen_tags'] = list(self.object.tags.all().values_list('id', flat=True))

        return super().get_context_data(**kwargs)


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


class ObservationAdminView(LoginRequiredMixin, TemplateView):
    """
    View the matrix of stars for users
    """
    template_name = 'observations.html'

    def get_data_for_construct_id(self, construct_id, course_id, date_from, date_to):
        IS_OTHER = False
        if course_id:
            all_students = Student.objects.filter(course=course_id)
        else:
            all_students = Student.objects.all()
        all_observations = Observation.objects.prefetch_related('students').filter(
            constructs__level__construct_id=construct_id,
            students__in=all_students
        )

        if date_from:
            all_observations = all_observations.filter(observation_date__gte=date_from)

        if date_to:
            all_observations = all_observations.filter(observation_date__lte=date_to)

        all_constructs_sublevels = LearningConstructSublevel.objects.filter(level__construct_id=construct_id)
        c_name = LearningConstruct.objects.filter(id=construct_id).first()
        if c_name:
            c_name = c_name.abbreviation + ' '
        else:
            IS_OTHER = True
            c_name = 'Observations without constructs '

        # Create data dicts
        student_map = {s.id: str(s) for s in all_students}
        construct_map = collections.OrderedDict(
            {csl.id: {'description': csl.description, 'name': csl.name.replace(c_name, '')} for csl in
             all_constructs_sublevels})

        if IS_OTHER:
            construct_map['other'] = {'Description': 'Observations without constructs', 'name': ' '}

        observations_map = {}
        matrix = {s.id: collections.defaultdict(set) for s in all_students}

        for observation in all_observations:
            if observation.constructs.count():
                for obs_construct in observation.constructs.all():
                    for obs_student in observation.students.filter(id__in=all_students):
                        matrix[obs_student.id][obs_construct.id].add(observation.id)
            else:
                for obs_student in observation.students.filter(id__in=all_students):
                    matrix[obs_student.id]['other'].add(observation.id)

        return {
            'student_map': student_map,
            'observations_map': observations_map,
            'construct_map': construct_map,
            'matrix': matrix,
            'c_name': c_name,
            'all_observations': all_observations,
            'IS_OTHER': IS_OTHER
        }

    def get_context_data(self, **kwargs):
        course_id = kwargs.get('course_id')
        all_constructs = LearningConstruct.objects.all()
        top_level_construct_map = {c.id: c.abbreviation for c in all_constructs}
        date_filtering_form = DateFilteringForm(self.request.GET)
        date_from = None
        date_to = None

        if date_filtering_form.is_valid():
            date_from = date_filtering_form.cleaned_data['date_from']
            date_to = date_filtering_form.cleaned_data['date_to']

        constructs_to_cover = LearningConstruct.objects.annotate(
            q_count=Count('learningconstructlevel__learningconstructsublevel__observation')
        ).order_by('-q_count')

        tables = [self.get_data_for_construct_id(cid, course_id, date_from, date_to) for cid in
                  constructs_to_cover.values_list('id', flat=True)]
        star_chart_tables = tables + [self.get_data_for_construct_id(None, course_id, date_from, date_to)]

        data = super().get_context_data(**kwargs)
        data.update({
            'star_chart_tables': star_chart_tables,
            'dot_plot_tables': tables,
            'top_level_construct_map': top_level_construct_map,
            'courses': Course.objects.all(),
            'course_id': course_id,
            'date_form': date_filtering_form,

        })
        return data


def current_observation(request):
    initial = {
        'course': request.session.get('course'),
        'grouping': request.session.get('grouping'),
        'constructs': '&constructs='.join([str(c) for c in request.session.get('constructs', [])]),
        'context_tags': '&context_tags='.join([str(ct) for ct in request.session.get('context_tags', [])]),
    }
    get_args = '&'.join([str(k) + '=' + str(v) for k, v in initial.items()])
    url = reverse('observation_view') + '?' + get_args
    return HttpResponseRedirect(url)


class ImportClassRoster(LoginRequiredMixin, TemplateView):
    template_name = 'import_class_roster.html'
    session_variable = 'class_roster_preview_data'

    def get(self, request, *args, **kwargs):
        # clear any residual data
        if self.session_variable in self.request.session.keys():
            del(self.request.session[self.session_variable])
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        file = request.FILES.get('uploadedFile')

        if not file:
            message = 'Please click "Choose File" below and select a file'
            return self.handle_error(message)

        try:
            fmt = file.name.split('.')[1]
            if fmt not in ACCEPTED_FILE_EXTENSIONS:
                message = 'Accepted file types are csv and excel'
                return self.handle_error(message)

        except Exception as err:
            message = 'Cannot determine file type.  Please make sure the file name ends with .csv, .xlsx or .xls'
            logger.exception('{}: {}'.format(message, err))
            return self.handle_error(message)

        try:
            # in memory file is in bytes, tablib wants csv data to be a string...
            if fmt == 'csv':
                file = io.TextIOWrapper(file, encoding='utf-8')

            file_data = Dataset().load(file.read())
            preview_data = ClassRoster(user=request.user).preview_rows(file_data)
            context = {'preview_data': preview_data.html}
            self.request.session[self.session_variable] = preview_data.json
            return render(request=request, template_name=self.template_name, context=context)

        except Exception as err:
            message = 'An error occurred preparing data for preview.'
            logger.exception(err)
            return self.handle_error(message)

    def handle_error(self, message):
        messages.error(request=self.request, message=message, fail_silently=True, extra_tags='alert alert-contrast alert-danger')
        return HttpResponseRedirect(reverse('import_class_roster'))


@login_required
def process_class_roster(request):
    try:
        dataset = Dataset()
        dataset.dict = json.loads(request.session[ImportClassRoster.session_variable])
        ClassRoster(user=request.user).process_rows(dataset)
        messages.success(request, message='File imported successfully', extra_tags='alert alert-contrast alert-success',
                         fail_silently=True)
        return HttpResponseRedirect(reverse('import_class_roster'))

    except Exception as err:
        message = 'An error occurred loading the file'
        logger.exception(err)
        messages.error(request, message=message, extra_tags='alert alert-contrast alert-danger', fail_silently=True)
        return HttpResponseRedirect(reverse('import_class_roster'))


@login_required
def export_class_roster(request):
    """
    Export course/student roster
    You can supply in the querystring:
    :fmt: defaults to xlsx.  determines file format to use
    :id: list of course ids, this filter overrides
    :user_id: can take a list of user_id which will be used to filter class owners
    """
    try:
        course_ids = request.GET.getlist('id')
        class_owners = [int(user) for user in request.GET.getlist('user_id')]
        fmt = request.GET.get('fmt') or 'xlsx'
        if fmt not in ACCEPTED_FILE_EXTENSIONS:
            raise InvalidFileFormatError('{} is not an acceptable export file format'.format(fmt))

        if course_ids:
            courses = Course.objects.filter(id__in=int(course_ids)).order_by('name')
        elif class_owners:
            courses = Course.objects.filter(owner_id__in=class_owners).order_by('name')
        else:
            courses = []

        return ClassRoster.export(user=request.user, queryset=courses, fmt=fmt)

    except InvalidFileFormatError as err:
        message = str(err)
        messages.error(request, message=message, extra_tags='alert alert-contrast alert-danger', fail_silently=True)
        return HttpResponseRedirect(reverse('import_class_roster'))

    except Exception as err:
        message = 'An error occurred exporting the file'
        logger.exception(err)
        messages.error(request, message=message, extra_tags='alert alert-contrast alert-danger', fail_silently=True)
        return HttpResponseRedirect(reverse('import_class_roster'))


def get_constructs(pk_list):
    return LearningConstructSublevel.objects.filter(pk__in=pk_list).\
        select_related('level', 'level__construct').prefetch_related('examples')


def get_recent_observations(owner, age=None):
    age = age or timedelta(hours=2)
    within_timeframe = timezone.now() - age
    return Observation.objects.filter(owner=owner, created__gte=within_timeframe).order_by('-created')


class BaseTagManagement(LoginRequiredMixin):
    model = ContextTag
    form_class = ContextTagForm
    success_url = reverse_lazy('setup')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['title'] = self.title
        return context


class CreateTag(BaseTagManagement, CreateView):
    template_name = 'context_tag.html'
    title = 'Create Tag'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        self.object.save()
        return super().form_valid(form)


class EditTag(BaseTagManagement, UpdateView):
    template_name = 'context_tag.html'
    title = 'Edit Tag'

    def get_queryset(self):
        return ContextTag.objects.filter(owner=self.request.user)

class ListTag(BaseTagManagement, ListView):
    title = 'Tags'
    template_name = 'context_tag_list.html'

    def get_queryset(self):
        return ContextTag.objects.filter(owner=self.request.user).order_by('id')
