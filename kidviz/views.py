import datetime
import datetime
import io
import json
import logging
import operator
from datetime import timedelta
from functools import reduce

from braces.views import JSONResponseMixin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.http import HttpResponseRedirect, JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, View, TemplateView, UpdateView, \
    CreateView, ListView
from related_select.views import RelatedSelectView
from tablib import Dataset

from kidviz.choices import TIME_WINDOW_CHOICES, WEEK_1
from kidviz.exceptions import InvalidFileFormatError
from kidviz.forms import ObservationForm, SetupForm, GroupingForm, ContextTagForm, \
    DateFilteringForm, DraftObservationForm
from kidviz.models import (
    ContextTag, Course, StudentGrouping, LearningConstructSublevel,
    LearningConstruct, StudentGroup, Student, Observation
)
from kidviz.resources import ClassRoster, ACCEPTED_FILE_EXTENSIONS

logger = logging.getLogger(__name__)


class SetupView(LoginRequiredMixin, FormView):
    template_name = 'setup.html'
    form_class = SetupForm

    def get(self, request, *args, **kwargs):
        if not self.request.user.has_perm("kidviz.add_observation"):
            return HttpResponseRedirect(reverse('observations_all'))
        return super().get(request, *args, **kwargs)

    def get_initial(self):
        initial = super(SetupView, self).get_initial()
        initial.update({
            'course': self.request.user.default_course,
            'grouping': self.request.session.get('grouping'),
            'constructs': self.request.session.get('constructs'),
            'context_tags': self.request.session.get('context_tags'),
            'request': self.request
        })

        if self.request.session.get('re_setup', False):
            draft_observation = Observation.objects.filter(is_draft=True, owner=self.request.user) \
                .order_by('-id') \
                .first()

            if draft_observation:
                initial['course'] = draft_observation.course

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
        self.request.session['curricular_focus'] = d['curricular_focus']

        if self.request.session.pop('reconfigure', None):
            tags = [tag.id for tag in tags]
            constructs = [construct.id for construct in get_constructs(pk_list=constructs)]
            draft_observation = Observation.objects.filter(is_draft=True, owner=self.request.user) \
                .update(construct_choices=constructs, tag_choices=tags)
        else:
            self.request.session['create_new'] = True

        return HttpResponseRedirect(reverse_lazy('observation_view'))

    def get_context_data(self, **kwargs):
        r = super(SetupView, self).get_context_data(**kwargs)
        r['form'].fields['grouping'].init_bound_field(r['form'].initial.get('course'))
        r['constructs'] = []

        for lc in LearningConstruct.objects.prefetch_related('levels', 'levels__sublevels',
                                                             'levels__sublevels__examples').all():
            construct = {
                'name': lc.name,
                'levels': [],
            }
            for lcl in lc.levels.all():
                level = {
                    'id': lcl.id,
                    'name': '{}) {}'.format(lcl.level, lcl.description),
                    'sublevels': []
                }
                for lcsl in lcl.sublevels.all():
                    sublevel = {
                        'id': lcsl.id,
                        'name': lcsl.name,
                        'description': lcsl.description,
                        'examples': lcsl.examples
                    }
                    level['sublevels'].append(sublevel)
                construct['levels'].append(level)
            r['constructs'].append(construct)

        r['curricular_focus_id'] = ContextTag.objects.get_or_create(
            text='Curricular Focus',
            curricular_focus=True
        )[0].id

        if self.request.session.pop('re_setup', None):
            r['re_setup'] = True
            self.request.session['reconfigure'] = True
        else:
            self.request.session.pop('reconfigure', None)

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
    """
    There are 3 ways of using this view:

    * Get action for observation form
    * Post action for observation form (saving new object)
    * Post action for observation form to get last sample. In this case
      any error should be ignored and form with last sample should be
      returned
    """
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
        if request.POST.get('use_recent_observation'):
            return self.get(request, *args, **kwargs)
        else:
            draft_observation = Observation.objects.filter(is_draft=True, owner=request.user) \
                .order_by('-id') \
                .first()

            original_image = request.POST.get('original_image', None)
            video = request.POST.get('video', None)

            # This is needed to update video or original_image when one of them is already set
            # and user want to change to the opposite.
            if draft_observation:
                draft_observation.update_draft_media(original_image, video)

            if request.POST.get('is_draft', None) == 'True':
                if request.session.get('create_new', None):
                    form = DraftObservationForm(request.POST, request.FILES)
                else:
                    form = DraftObservationForm(request.POST, request.FILES, instance=draft_observation)

                form.is_valid()

                # Not doing commit=False to save manyToMany relations.
                obj = form.save()

                # When user reset image or video to default state and then updates draft.
                if not 'original_image' in request.POST and not 'video' in request.POST:
                    obj.reset_media()

                request.session.pop('create_new', None)

                if request.POST.get('back_to_setup', None) == 'True':
                    request.session['re_setup'] = True
                    return HttpResponseRedirect(reverse_lazy('setup'))

                messages.add_message(request, messages.SUCCESS, 'Draft Created.')
                return HttpResponseRedirect(self.get_success_url())
            else:
                form = ObservationForm(request.POST, request.FILES, instance=draft_observation)
                return self.form_valid(form)

    def get_context_data(self, **kwargs):
        session_course = self.request.session.get('course')
        session_grouping = self.request.session.get('grouping')
        session_construct_choices = self.request.session.get('constructs') or []
        session_tags = self.request.session.get('context_tags') or []
        session_focus = self.request.session.get('curricular_focus') or ''
        last_observation_id = self.request.session.get('last_observation_id')
        create_new = self.request.session.get('create_new', False)

        course = Course.objects.filter(pk=session_course).first()
        grouping = None
        if session_grouping:
            grouping = StudentGrouping.objects.filter(pk=session_grouping).first()

        self.initial.update({
            'name': '{} Observed'.format(course.name),
            'course': course, 'grouping': grouping, 'tag_choices': session_tags,
            'construct_choices': session_construct_choices, 'owner': self.request.user,
            'curricular_focus': session_focus
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
        kwargs['curricular_focus'] = session_focus
        kwargs['construct_choices'] = get_constructs(pk_list=session_construct_choices)
        kwargs['chosen_students'] = json.dumps([int(item) for item in self.request.POST.getlist('students')])
        kwargs['chosen_constructs'] = json.dumps([int(item) for item in self.request.POST.getlist('constructs')])
        kwargs['chosen_tags'] = chosen_tags
        kwargs['recent_observation'] = get_recent_observations(owner=self.request.user).first()

        # Create new instance of observation form to clear error.
        # use_recent_observation is send for Use Last Sample action.
        if self.request.POST.get('use_recent_observation'):
            kwargs['use_last_sample'] = True
            kwargs['form'] = ObservationForm(initial=self.initial)
        
        if not self.request.POST.get('use_recent_observation') and not create_new:
            draft_observation = Observation.objects.filter(is_draft=True, owner=self.request.user) \
                .order_by('-id') \
                .prefetch_related('students') \
                .prefetch_related('constructs') \
                .prefetch_related('tags') \
                .first()

            if draft_observation:
                kwargs.update({
                    'draft_observation': draft_observation,
                    'chosen_students': json.dumps(
                        list(map(lambda student: student.pk, draft_observation.students.all()))), 
                    'chosen_tags': list(map(lambda tag: tag.pk, draft_observation.tags.all())),
                    'chosen_constructs': list(map(
                        lambda construct: construct.pk, draft_observation.constructs.all())),
                    'form': ObservationForm(instance=draft_observation)
                })

                created = timezone.localtime(draft_observation.created)
                is_today = created.day == datetime.date.today().day

                if is_today:
                    kwargs['header'] = 'Draft observation {}'.format(created.strftime('%-I:%-M %p'))
                else:
                    kwargs['header'] = 'Draft observation {}'.format(created.strftime('%-m-%-d-%y %-I:%-M %p'))

        kwargs['use_draft'] = True
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        obj = form.save()

        # Do not add draft observation to session.
        if self.request.POST.get('is_draft', 'False') == 'False':
            self.request.session['last_observation_id'] = obj.id

        return super().form_valid(form)


class ObservationDetailView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    model = Observation
    template_name = 'observation.html'
    form_class = ObservationForm
    success_message = 'Observation Updated'
    success_url = reverse_lazy('observation_view')

    def get_context_data(self, **kwargs):
        available_tags = self.object.tag_choices
        kwargs['is_today'] = self.object.created.day == datetime.date.today().day
        kwargs['created'] = self.object.created
        kwargs['course'] = self.object.course
        kwargs['grouping'] = self.object.grouping
        kwargs['tags'] = ContextTag.objects.filter(owner=self.request.user, pk__in=available_tags)
        kwargs['construct_choices'] = get_constructs(pk_list=self.object.construct_choices)
        kwargs['chosen_students'] = json.dumps(list(self.object.students.all().values_list('id', flat=True)))
        kwargs['chosen_constructs'] = json.dumps(list(self.object.constructs.all().values_list('id', flat=True)))
        kwargs['chosen_tags'] = list(self.object.tags.all().values_list('id', flat=True))
        kwargs['use_draft'] = False

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


class DefaultCourseView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        course_id = request.POST.get('course', '')
        if not course_id.isdigit():
            return HttpResponseBadRequest()  # TODO not sure if this should be bad request or just 204 No Content.

        course = get_object_or_404(Course, pk=int(course_id))
        user = request.user
        user.default_course = course
        user.save()

        return JsonResponse({'success': True})


class ObservationAjax(LoginRequiredMixin, View):

    def is_valid_date(self, date_string):
        try:
            if not date_string:
                return True
            datetime.datetime.strptime(date_string, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def is_valid_request(self, course_id, date_from, date_to):
        return (
            course_id.isdigit() or not course_id
            and self.is_valid_date(date_from)
            and self.is_valid_date(date_to)
        )

    def post(self, request, *args, **kwargs):
        self.request = request
        course_id = request.POST.get('course', '')
        date_from = request.POST.get('date_from', '')
        date_to = request.POST.get('date_to', '')
        if self.is_valid_request(course_id, date_from, date_to):
            observations = Observation.objects.all()
            if course_id:
                observations = observations.filter(course=course_id)

            if date_from:
                observations = observations.filter(observation_date__gte=date_from)

            if date_to:
                observations = observations.filter(observation_date__lte=date_to)

            constructs = set()
            for observation in observations:
                constructs.update(list(observation.constructs.all()))

            constructs_data = [{'id': c.id, 'value': c.name} for c in list(constructs)]
            return JsonResponse({'success': True, 'data': constructs_data})

        return HttpResponseBadRequest()


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
                student = Student.objects.get(id=student_id, status=Student.ACTIVE)
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

    def selected_chart(self):
        get = self.request.GET or {}
        chart_keys = ['chart_v1', 'chart_v2', 'chart_v3',
            'chart_v1_vertical', 'heat_map', 'chart_v4']
        for key in chart_keys:
            if key in get:
                return key

        return chart_keys[0]

    def get_context_data(self, **kwargs):
        course_id = kwargs.get('course_id')
        date_filtering_form = self._init_filter_form(self.request.GET)

        date_from = None
        date_to = None
        selected_constructs = None
        tags = None
        time_window = WEEK_1

        if date_filtering_form.is_valid():
            date_from = date_filtering_form.cleaned_data['date_from']
            date_to = date_filtering_form.cleaned_data['date_to']
            selected_constructs = date_filtering_form.cleaned_data['constructs']
            tags = date_filtering_form.cleaned_data['tags']
            time_window = date_filtering_form.cleaned_data['time_window'] or WEEK_1
            courses = date_filtering_form.cleaned_data['courses']

            # If there aren't any query params use default course.
            if self.request.GET:
                if courses:
                    course_id = [course.id for course in courses]
                else:
                    course_id = None

        observations = Observation.get_observations(
            course_id, date_from, date_to, tags)
        time_observations = Observation.get_time_observations(observations, time_window)

        constructs = LearningConstruct.objects.prefetch_related('levels', 'levels__sublevels').all()
        all_students = Student.get_students_by_course(course_id)

        star_matrix = {}
        dot_matrix = {}
        observation_without_construct = {}
        star_matrix_by_class = Observation.initialize_star_matrix_by_class(constructs, course_id)

        for construct in constructs:
            star_matrix[construct] = {}
            dot_matrix[construct] = {}

            for student in all_students:
                star_matrix[construct][student] = {}
                observation_without_construct[student] = []

                for level in construct.levels.all():
                    for sublevel in level.sublevels.all():
                        star_matrix[construct][student][sublevel] = []
                        dot_matrix[construct][sublevel] = []

        for observation in observations:
            students = observation.students.all()
            sublevels = observation.constructs.all()
            for student in students:
                if student not in all_students:
                    continue

                if not sublevels:
                    observation_without_construct[student].append(observation)

                for sublevel in sublevels:
                    construct = sublevel.level.construct
                    star_matrix[construct][student][sublevel].append(observation)
                    dot_matrix[construct][sublevel].append(observation)
                    star_matrix_by_class[construct][observation.course][student][sublevel].append(observation)

        data = super().get_context_data(**kwargs)
        data.update({
            'star_matrix': star_matrix,
            'dot_matrix': dot_matrix,
            'obseravtion_without_construct': observation_without_construct,
            'all_observations': observations,
            'selected_constructs': selected_constructs,
            'courses': Course.objects.all(),
            'course_id': course_id,
            'filtering_form': date_filtering_form,
            'selected_chart': self.selected_chart(),
            'star_matrix_vertical': Observation.get_vertical_stars(star_matrix),
            'star_matrix_by_class': star_matrix_by_class,
            'star_chart_4': Observation.create_star_chart_4(
                time_observations, all_students, constructs),
            'time_observations_count': time_observations.count(),
            'COLORS_DARK': json.dumps(LearningConstructSublevel.COLORS_DARK),
            'time_window_display': dict(
                    date_filtering_form.fields['time_window'].choices)[time_window]
        })
        return data

    def _init_filter_form(self, GET_DATA):
        return DateFilteringForm(GET_DATA, initial={
            'course': GET_DATA.get('course', None),
            'date_from': GET_DATA.get('date_from', None),
            'date_to': GET_DATA.get('date_to', None),
            'constructs': GET_DATA.get('constructs', None),
            'tags': GET_DATA.get('tags', None),
            'time_window': GET_DATA.get('time_window', None)
        })


class TeacherObservationView(LoginRequiredMixin, TemplateView):
    """
    New matrix chart sorted by teachers
    """
    template_name = 'teachers_observations.html'

    def get_context_data(self, **kwargs):
        course_id = kwargs.get('course_id')
        date_filtering_form = DateFilteringForm(self.request.GET)
        date_from = None
        date_to = None
        selected_constructs = None
        tags = None

        if date_filtering_form.is_valid():
            date_from = date_filtering_form.cleaned_data['date_from']
            date_to = date_filtering_form.cleaned_data['date_to']
            selected_constructs = date_filtering_form.cleaned_data['constructs']
            tags = date_filtering_form.cleaned_data['tags']
            courses = date_filtering_form.cleaned_data['courses']

            # If there aren't any query params use default course.
            if self.request.GET:
                if courses:
                    course_id = [course.id for course in courses]
                else:
                    course_id = None

        observations = Observation.objects \
            .prefetch_related('students') \
            .prefetch_related('constructs') \
            .prefetch_related('tags') \
            .prefetch_related('constructs__level') \
            .prefetch_related('constructs__level__construct') \
            .order_by('owner', 'constructs') \
            .all()

        if course_id:
            observations = observations.filter(course__in=course_id)

        if date_from:
            observations = observations.filter(observation_date__gte=date_from)

        if date_to:
            observations = observations.filter(observation_date__lte=date_to)

        if tags:
            tag_ids = [tag.id for tag in tags]
            observations = observations.filter(tags__in=tag_ids)

        constructs = LearningConstruct.objects.all()

        all_students = Student.objects.filter(status=Student.ACTIVE)
        if course_id:
            all_students = all_students.filter(course__in=course_id)

        dot_matrix = {}

        teachers = get_user_model().objects.filter(kidviz_observation_owner__isnull=False)
        sublevels = LearningConstructSublevel.objects.filter(observation__isnull=False)

        for teacher in teachers:
            dot_matrix[teacher] = {}

            for sublevel in sublevels:
                dot_matrix[teacher][sublevel] = []

            dot_matrix[teacher]['No construct'] = []

        for observation in observations:
            sublevels = observation.constructs.all()

            if not sublevels:
                dot_matrix[observation.owner]['No construct'].append(observation)

            for sublevel in sublevels:
                teacher = observation.owner
                dot_matrix[teacher][sublevel].append(observation)

        data = super().get_context_data(**kwargs)
        data.update({
            'dot_matrix': dot_matrix,
            'all_observations': observations,
            'selected_constructs': selected_constructs,
            'courses': Course.objects.all(),
            'course_id': course_id,
            'filtering_form': date_filtering_form
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
            del (self.request.session[self.session_variable])
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        file = request.FILES.get('uploadedFile')

        if not file:
            message = 'Please click "Choose File" below and select a file'
            return self.handle_error(message)

        try:
            fmt = file.name.split('.')[-1]
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
        messages.error(request=self.request, message=message, fail_silently=True)
        return HttpResponseRedirect(reverse('import_class_roster'))


@login_required
def process_class_roster(request):
    try:
        dataset = Dataset()
        dataset.dict = json.loads(request.session[ImportClassRoster.session_variable])
        ClassRoster(user=request.user).process_rows(dataset)
        messages.success(request, message='File imported successfully', fail_silently=True)
        return HttpResponseRedirect(reverse('import_class_roster'))

    except Exception as err:
        message = 'An error occurred loading the file'
        logger.exception(err)
        messages.error(request, message=message, fail_silently=True)
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
        messages.error(request, message=message, fail_silently=True)
        return HttpResponseRedirect(reverse('import_class_roster'))

    except Exception as err:
        message = 'An error occurred exporting the file'
        logger.exception(err)
        messages.error(request, message=message, fail_silently=True)
        return HttpResponseRedirect(reverse('import_class_roster'))


def get_constructs(pk_list):
    return LearningConstructSublevel.objects.filter(pk__in=pk_list). \
        select_related('level', 'level__construct').prefetch_related('examples')


def get_recent_observations(owner, age=None):
    age = age or timedelta(hours=2)
    within_timeframe = timezone.now() - age
    return Observation.objects.filter(owner=owner, created__gte=within_timeframe).order_by('-created')


class BaseTagManagement(LoginRequiredMixin):
    model = ContextTag
    form_class = ContextTagForm
    success_url = reverse_lazy('tag_list')

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


class FloatingStudents(ListView):
    model = Student
    template_name = 'floating_report.html'

    def get_queryset(self):
        return Student.objects.filter(course__isnull=True).order_by('pk')


class DoubledStudents(ListView):
    model = Student
    template_name = 'doubled_report.html'

    def get_queryset(self):
        return Student.objects.annotate(count=Count('course')) \
            .filter(count__gte=2).prefetch_related('course_set').order_by('pk')


class HomonymStudents(ListView):
    model = Student
    template_name = 'homonym_report.html'

    def get_queryset(self):
        student_names = Student.objects \
            .order_by('last_name', 'first_name') \
            .values('last_name', 'first_name') \
            .annotate(count=Count('id')) \
            .filter(count__gte=2)

        name_tuples = [(s['first_name'], s['last_name']) for s in student_names]
        if not name_tuples:
            return Student.objects.none()

        query = reduce(operator.or_, (Q(first_name=f, last_name=l) for f, l in name_tuples))

        return Student.objects.filter(query)

    def get_context_data(self, **kwargs):
        data = super().get_context_data()
        objects = data['object_list']
        grouped_data = dict()
        for object in objects:
            name = '{} {}'.format(object.first_name, object.last_name)
            if name in grouped_data:
                grouped_data[name].append(object)
            else:
                grouped_data[name] = [object]
        data['object_list'] = grouped_data
        return data


class StudentReportAjax(View):

    def validate_floating(self, student_id, action):
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return False, None

        if action not in ['active', 'inactive']:
            return False, None

        return True, student

    def validate_doubled(self, student_id, action, course_ids):
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return False, None

        if action not in ['split']:
            return False, None

        count = Course.objects.filter(pk__in=course_ids, students__in=[student_id]).count()
        if count != len(course_ids):
            return False, None

        return True, student

    def validate_homonym(self, student_ids, name, action):
        students = Student.objects.filter(pk__in=student_ids)
        is_valid = True

        if not (student_ids and name and action):
            is_valid = False

        elif any(slugify(student.name) != name for student in students):
            is_valid = False

        elif action not in ['merge']:
            is_valid = False

        return is_valid, list(students)

    def post(self, request):
        self.request = request
        report = request.POST.get('report', '')

        if report == 'floating':
            student_id = request.POST.get('student_id', '')
            action = request.POST.get('action', '')
            is_valid, student = self.validate_floating(student_id, action)
            if is_valid:
                student.status = action
                student.save()
                return JsonResponse({
                    'success': True,
                    'status': student.status
                })

        elif report == 'doubled':
            student_id = request.POST.get('student_id', '')
            action = request.POST.get('action', '')
            course_ids = request.POST.getlist('course_ids[]', [])

            is_valid, student = self.validate_doubled(student_id, action, course_ids)

            if is_valid and student:
                all_courses = Course.objects.filter(students__pk=student.pk)
                # If user select all courses to split choose one base.
                base_course_pk = None

                if len(course_ids) == all_courses.count():
                    base_course_pk = all_courses.first().pk

                courses_to_split = Course.objects \
                    .filter(pk__in=course_ids, students__pk=student.pk) \
                    .exclude(pk=base_course_pk)

                for course in courses_to_split:
                    student.split_to_new(course)

                return JsonResponse({'success': True})

        elif report == 'homonym':
            student_ids = request.POST.getlist('student_ids[]', [])
            name = request.POST.get('name', '')
            action = request.POST.get('action', '')

            is_valid, students = self.validate_homonym(student_ids, name, action)
            if is_valid and students:
                # Select student with the higher grade level
                selected = students[0]
                for student in students:
                    if student.grade_level > selected.grade_level:
                        selected = student

                for student in students:
                    if student != selected:
                        selected.reassign(student)
                        student.delete()

                return JsonResponse({
                    'success': True,
                    'root_student_id': selected.pk
                })

        return HttpResponseBadRequest()


class DismissDraft(LoginRequiredMixin, View):
    """View used to dismiss draft."""

    def get(self, request, *args, **kwargs):
        Observation.objects.filter(is_draft=True) \
            .order_by('-id') \
            .first() \
            .delete()

        messages.add_message(self.request, messages.SUCCESS, 'Draft Dismissed.')
        return HttpResponseRedirect(reverse_lazy('observation_view'))


class WorkQueue(LoginRequiredMixin, ListView):
    """View used to display work queue."""
    template_name = 'work_queue.html'
    paginate_by = 10

    def get_queryset(self):
        return Observation.objects \
            .prefetch_related('students') \
            .filter(owner=self.request.user, constructs=None)
            
