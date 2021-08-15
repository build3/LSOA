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

from kidviz.exceptions import InvalidFileFormatError
from kidviz.forms import (
    ObservationForm, SetupForm, GroupingForm, ContextTagForm,
    CourseFilterForm, DateFilteringForm, DraftObservationForm, StudentFilterForm, SetupSaveForm,
    ObservationByIDForm
)
from kidviz.models import (
    ContextTag, Course, StudentGrouping, LearningConstructSublevel,
    LearningConstruct, Setup, StudentGroup, Student, Observation
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

        learning_constructs = []

        for lc in LearningConstruct.objects.prefetch_related('levels', 'levels__sublevels',
                                                             'levels__sublevels__examples').all():
            if lc.abbreviation == 'ToML':
                learning_constructs.insert(0, lc)
            else:
                learning_constructs.append(lc)

        for lc in learning_constructs:
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

        self.request.session.pop('read_only', None)

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
        self.request.session.pop('read_only', None)

        if not self.request.session.get('course'):
            return HttpResponseRedirect(reverse('setup'))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.POST.get('use_recent_observation'):
            return self.get(request, *args, **kwargs)
        else:
            if request.POST.get('is_draft', None) == 'True':
                if request.session.get('create_new', None):
                    form = DraftObservationForm(request.POST, request.FILES)
                    message = 'Draft Created.'
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
                        form = DraftObservationForm(request.POST, request.FILES, instance=draft_observation)
                        message = 'Draft Updated.'
                    else:
                        form = DraftObservationForm(request.POST, request.FILES)
                        message = 'Draft Created.'

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

                messages.add_message(request, messages.SUCCESS, message)
                return HttpResponseRedirect(self.get_success_url())
            else:
                form = ObservationForm(request.POST, request.FILES)
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
        kwargs['has_video'] = False

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
        kwargs['tags'] = ContextTag.objects.filter(Q(owner=self.request.user) | Q(owner__isnull=True), pk__in=available_tags)
        kwargs['construct_choices'] = get_constructs(pk_list=self.object.construct_choices)
        kwargs['chosen_students'] = json.dumps(list(self.object.students.all().values_list('id', flat=True)))
        kwargs['chosen_constructs'] = json.dumps(list(self.object.constructs.all().values_list('id', flat=True)))
        kwargs['chosen_tags'] = list(self.object.tags.all().values_list('id', flat=True))
        kwargs['use_draft'] = False
        kwargs['has_video'] = self.object.video != ''
        kwargs['read_only'] = self.request.session.get('read_only', False)

        return super().get_context_data(**kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['read_only'] = self.request.session.get('read_only', False)
        kwargs['initial'] = {}

        return kwargs

    def get_success_url(self):
        return reverse('observation_detail_view', args=(self.object.id,))

    def post(self, request, pk):
        self.object = self.get_object()

        # When user reset image or video to default state and then updates draft.
        if request.POST.get('has_been_reset', False) == 'True':
            self.object.reset_media()
        else:
            original_image = request.POST.get('original_image', None)
            video = request.POST.get('video', None)
            self.object.update_draft_media(original_image, video)

        if request.POST.get('back_to_setup', None) == 'True':
            form = DraftObservationForm(request.POST, request.FILES, instance=self.object)
            form.is_valid()
            form.save()

            request.session['re_setup'] = True
            return HttpResponseRedirect(reverse_lazy('setup'))

        return super().post(request, pk)


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
        chart_keys = ['student_view', 'construct_view', 'construct_heat_map', 'timeline_view']
        for key in chart_keys:
            if key in get:
                return key

        return chart_keys[0]

    def get_context_data(self, **kwargs):
        self.request.session.pop('read_only', None)

        session_course = self.request.session.get('course')
        star_courses = self.request.session.get('star_courses', [])
        course_ids = list(dict.fromkeys([self.request.user.get_course(session_course)] + star_courses))
        date_filtering_form = self._init_filter_form(self.request.GET, course_ids)

        date_from = None
        date_to = None
        selected_constructs = None
        tags = None
        learning_constructs = []
        show_no_construct = True

        if date_filtering_form.is_valid():
            date_from = date_filtering_form.cleaned_data['date_from']
            date_to = date_filtering_form.cleaned_data['date_to']
            selected_constructs = date_filtering_form.cleaned_data['constructs']
            tags = date_filtering_form.cleaned_data['tags']
            courses = date_filtering_form.cleaned_data['courses']
            learning_constructs = date_filtering_form.cleaned_data['learning_constructs']
            # If there aren't any query params use default course.
            if self.request.GET:
                if courses:
                    course_ids = [course.id for course in courses]
                    self.request.session['star_courses'] = course_ids

        (observations, star_chart_4_obs) = Observation.get_observations(
            course_ids, date_from, date_to, tags, learning_constructs)

        all_constructs = LearningConstruct.objects.prefetch_related('levels', 'levels__sublevels').all()

        all_constructs_sorted = []

        for construct in all_constructs:
                if construct.abbreviation == 'ToML':
                    all_constructs_sorted.insert(0, construct)
                else:
                    all_constructs_sorted.append(construct)

        constructs_wo_no_construct = [
            construct
            for construct in learning_constructs
            if construct != LearningConstruct.NO_CONSTRUCT
        ]

        if learning_constructs and not LearningConstruct.NO_CONSTRUCT in learning_constructs:
            constructs = []

            for construct in all_constructs.filter(id__in=learning_constructs):
                if construct.abbreviation == 'ToML':
                    constructs.insert(0, construct)
                else:
                    constructs.append(construct)

            show_no_construct = False

        elif LearningConstruct.NO_CONSTRUCT in learning_constructs:
            constructs = []

            for construct in all_constructs.filter(id__in=constructs_wo_no_construct):
                if construct.abbreviation == 'ToML':
                    constructs.insert(0, construct)
                else:
                    constructs.append(construct)

        else:
            constructs = all_constructs_sorted

        all_students = Student.get_students_by_course(course_ids)
        courses = Course.get_courses(course_ids)

        star_matrix = {}
        dot_matrix = Observation.initialize_dot_matrix_by_class(all_constructs_sorted, courses)
        observation_without_construct = {}
        star_matrix_by_class = Observation.initialize_star_matrix_by_class(constructs, courses)

        if constructs:
            for construct in constructs:
                star_matrix[construct] = {}

                for student in all_students:
                    star_matrix[construct][student] = {}
                    observation_without_construct[student] = []

                    for level in construct.levels.all():
                        for sublevel in level.sublevels.all():
                            star_matrix[construct][student][sublevel] = []
        else:
            for student in all_students:
                observation_without_construct[student] = []

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

                    if construct not in constructs:
                        continue

                    star_matrix[construct][student][sublevel].append(observation)

                    if observation.course:
                        dot_matrix[construct][observation.course][sublevel].append(observation)

                        # If star_matrix_by_class does not contains key with student initialize it.
                        # This can happen when user changed student's course and observation stayed with old one.
                        try:
                            star_matrix_by_class[construct][observation.course][student][sublevel].append(observation)
                        except KeyError:
                            star_matrix_by_class[construct][observation.course][student] = {}

                            for level in construct.levels.all():
                                for sub in level.sublevels.all():
                                    star_matrix_by_class[construct][observation.course][student][sub] = []

                            star_matrix_by_class[construct][observation.course][student][sublevel].append(observation)

        min_date = Observation.get_min_date_from_observation(star_chart_4_obs)
        star_chart_4, star_chart_4_dates = Observation.create_star_chart_4(
                star_chart_4_obs, all_constructs_sorted, courses, min_date)

        data = super().get_context_data(**kwargs)
        data.update({
            'star_matrix': star_matrix,
            'dot_matrix': dot_matrix,
            'observation_without_construct': observation_without_construct,
            'all_observations': observations,
            'selected_constructs': selected_constructs,
            'courses': Course.objects.all(),
            'course_id': course_ids,
            'filtering_form': date_filtering_form,
            'selected_chart': self.selected_chart(),
            'star_matrix_by_class': star_matrix_by_class,
            'star_chart_4': star_chart_4,
            'COLORS_DARK': json.dumps(LearningConstructSublevel.COLORS_DARK),
            'min_date': min_date,
            'max_date': Observation.get_max_date_from_observations(star_chart_4_obs),
            'star_chart_4_dates': json.dumps(star_chart_4_dates),
            'observations_count': star_chart_4_obs.filter(constructs__isnull=False).count(),
            'show_no_construct': show_no_construct,
            'constructs_reports': True,
            'filtered_constructs': list(map(int, constructs_wo_no_construct))
        })

        return data

    def _init_filter_form(self, GET_DATA, courses):
        return DateFilteringForm(GET_DATA, initial={
            'course': GET_DATA.get('course', None),
            'date_from': GET_DATA.get('date_from', None),
            'date_to': GET_DATA.get('date_to', None),
            'constructs': GET_DATA.get('constructs', None),
            'tags': GET_DATA.get('tags', None),
            'learning_construct': GET_DATA.get('learning_construct', None)
        })


class StudentsTimelineView(LoginRequiredMixin, TemplateView):
    template_name = 'students_timeline_view.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        self.request.session.pop('read_only', None)

        # Get default course or first course in database.
        course = self.request.user.get_course(self.request.session.get('course'))
        students = None

        # Check if course was changed.
        if not self.request.GET.get('course', None):
            if isinstance(course, int):
                course = get_object_or_404(Course, id=course)

            course_filter_form = CourseFilterForm(initial={'course': course.id})
        else:
            course_filter_form = CourseFilterForm(self.request.GET)

        if course_filter_form.is_valid():
            course = course_filter_form.cleaned_data['course']

        queryset = course.students.all()
        filter_form = StudentFilterForm(self.request.GET, queryset=queryset)
        chosen_students = self.request.GET.getlist('students')

        if filter_form.is_valid():
            students = filter_form.cleaned_data['students']
        else:
            # This is required to display report when one student belong to the class but others don't.
            #
            # For example when user selects two students in class A and then clicks submit two
            # reports are going to show. Then if he change class to B and do not change students
            # (let's say one of the students belongs to class B as well)
            # system should display report for that one student even though form is invalid.
            if chosen_students:
                students = [Student.objects.get(id=student_id) for student_id in chosen_students
                    if int(student_id) in queryset.values_list('id', flat=True)]

        observations = None

        if students:
            observations = Observation.objects.filter(students__in=students) \
                .prefetch_related('students') \
                .prefetch_related('constructs') \
                .prefetch_related('tags') \
                .prefetch_related('constructs__level') \
                .prefetch_related('constructs__level__construct') \
                .prefetch_related('course')

        if observations:
            constructs = LearningConstruct.objects.prefetch_related('levels', 'levels__sublevels').all()
            min_date = Observation.get_min_date_from_observation(observations)

            star_chart, dates = Observation.create_student_timeline(
                observations, students, constructs, min_date)

            data.update({
                'star_chart': star_chart,
                'dates': json.dumps(dates),
                'min_date': min_date,
                'max_date': Observation.get_max_date_from_observations(observations),
                'COLORS_DARK': json.dumps(LearningConstructSublevel.COLORS_DARK),
                'observations_count': observations.filter(constructs__isnull=False).count(),
            })

        data.update({
            'filter_form': filter_form,
            'course_filter_form': course_filter_form,
            'students': students,
            'course_id': course.id,
        })

        return data


class TeacherObservationView(LoginRequiredMixin, TemplateView):
    """
    New matrix chart sorted by teachers
    """
    template_name = 'teachers_observations.html'

    def get_context_data(self, **kwargs):
        self.request.session.pop('read_only', None)

        self.filtering_form = DateFilteringForm(self.request.GET)
        data = super().get_context_data(**kwargs)

        if self.request.GET.get('from', None):
            if self.filtering_form.is_valid():
                observations = self._filter_observations()

                data.update({
                    **self._base_context_data,
                    'dot_matrix': self._calculate_dot_matrix(observations),
                    'all_observations': observations,
                })

                return data

        data.update(self._default_context_data)
        return data

    def _filter_observations(self):
        date_from = self.filtering_form.cleaned_data.get('date_from')
        date_to = self.filtering_form.cleaned_data.get('date_to')
        selected_constructs = self.filtering_form.cleaned_data.get('constructs')
        tags = self.filtering_form.cleaned_data.get('tags')
        learning_construct = self.filtering_form.cleaned_data.get('learning_construct')

        observations = self._all_observations

        if date_from:
            observations = observations.filter(observation_date__gte=date_from)

        if date_to:
            observations = observations.filter(observation_date__lte=date_to)

        if tags:
            tag_ids = [tag.id for tag in tags]
            observations = observations.filter(tags__in=tag_ids)

        if selected_constructs:
            observations = observations.filter(constructs__id__in=selected_constructs)

        if learning_construct:
            if learning_construct != 'NO_CONSTRUCT':
                observations = observations.filter(constructs__level__construct__id=learning_construct)
            else:
                observations = observations.filter(no_constructs=True)

        return observations

    @property
    def _all_observations(self):
        return Observation.objects \
            .prefetch_related('students') \
            .prefetch_related('constructs__level__construct') \
            .prefetch_related('tags') \
            .prefetch_related('grouping__groups__students') \
            .select_related('owner') \
            .order_by('owner', 'constructs') \
            .all()

    def _calculate_dot_matrix(self, observations):
        dot_matrix = {}

        teachers = get_user_model().objects.filter(kidviz_observation_owner__isnull=False).distinct()
        sublevels = LearningConstructSublevel.objects.filter(observation__isnull=False).distinct()

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

        return dot_matrix

    @property
    def _base_context_data(self):
        return {
            'courses': Course.objects.all(),
            'course_id': None,
            'filtering_form': self.filtering_form
        }

    @property
    def _default_context_data(self):
        return {
            **self._base_context_data,
            'dot_matrix': [],
            'all_observations': None,
        }


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
        self.request.session.pop('read_only', None)

        return Observation.objects.filter(
            Q(owner=self.request.user, constructs=None, is_draft=False) |
            Q(owner=self.request.user, is_draft=True)
        ).distinct()


class RemoveDraft(LoginRequiredMixin, View):
    def post(self, request, pk):
        Observation.objects.filter(pk=pk, is_draft=True, owner=request.user).delete()
        messages.add_message(self.request, messages.SUCCESS, 'Draft removed.')
        return HttpResponseRedirect(reverse_lazy('work-queue'))


class StartNewObservation(LoginRequiredMixin, View):
    def get(self, request):
        self.request.session['create_new'] = True
        return HttpResponseRedirect(reverse_lazy('observation_view'))


class SaveUserSetupView(LoginRequiredMixin, FormView):
    form_class = SetupSaveForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = Setup.objects.filter(user=self.request.user).first()

        return kwargs

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.user = self.request.user
        instance.save()
        form.save_m2m()

        return JsonResponse({'success': True}, safe=True)

    def form_invalid(self, form):
        return JsonResponse({'errors': form.errors}, safe=True, status=400)


class GetUserSetup(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        setup = get_object_or_404(Setup, user=request.user)

        return JsonResponse(
            {
                'course': setup.course.id if setup.course else '',
                'grouping': setup.grouping.id if setup.grouping else '',
                'context_tags': list(setup.context_tags.all().values_list('id', flat=True)),
                'constructs': list(setup.constructs.all().values_list('id', flat=True)),
            },
            safe=True
        )


class AdminObservationsByID(LoginRequiredMixin, FormView):
    form_class = ObservationByIDForm
    template_name = "admin_observation_by_id.html"

    def form_valid(self, form):
        self.request.session['read_only'] = True

        return HttpResponseRedirect(
            reverse('observation_detail_view', args=(form.data['observation_id'],))
        )
