from django.contrib import admin, messages
from django import forms
from import_export import resources, fields
from import_export.admin import ImportExportActionModelAdmin

from lsoa.resources import ACCEPTED_FILE_FORMATS, ClassRoster
from .models import Course, LearningConstruct, LearningConstructLevel, LearningConstructSublevel, \
    LearningConstructSublevelExample, Observation, Student, StudentGroup, StudentGrouping

admin.site.site_header = 'LSOA Settings'
admin.site.site_title = 'LSOA Admin'
admin.site.site_url = '/'
admin.site.index_title = 'Settings'


def advance_grade(modeladmin, request, queryset):
    processed = 0
    for row in queryset:
        row.advance_grade_level()
        processed += 1
    msg = '{} students updated'.format(processed)
    modeladmin.message_user(request, message=msg.strip(), level=messages.INFO)


advance_grade.short_description = 'Advance Grade'


def export_class_roster(modeladmin, request, queryset):
    return ClassRoster.export(user=request.user, queryset=queryset)


export_class_roster.short_description = 'Export selected course rosters'


class StudentResource(resources.ModelResource):
    id = fields.Field(column_name='Student ID', attribute='id')
    first_name = fields.Field(column_name='First Name', attribute='first_name')
    last_name = fields.Field(column_name='Last Name', attribute='last_name')
    nickname = fields.Field(column_name='Nickname', attribute='nickname')
    grade_level = fields.Field(column_name='Grade Level', attribute='grade_level')

    class Meta:
        model = Student
        fields = ('id', 'first_name', 'last_name', 'nickname', 'grade_level')
        export_order = fields
        skip_unchanged = True
        report_skipped = True


class CourseResource(resources.ModelResource):
    id = fields.Field(column_name='Course ID', attribute='id')
    name = fields.Field(column_name='Course Name', attribute='name')
    owner = fields.Field(column_name='Course Owner', attribute='owner')
    grade_level = fields.Field(column_name='Grade Level', attribute='grade_level')

    class Meta:
        model = Student
        fields = ('id', 'name', 'grade_level', 'owner',)
        export_order = fields
        skip_unchanged = True
        report_skipped = True


@admin.register(Student)
class StudentAdmin(ImportExportActionModelAdmin):
    formats = ACCEPTED_FILE_FORMATS
    actions = [advance_grade, ]
    resource_class = StudentResource
    list_display = ('first_name', 'nickname', 'last_name', 'grade_level', 'modified')
    list_filter = ('grade_level',)
    preserve_filters = True
    search_fields = ('last_name', 'first_name', 'nickname',)
    ordering = ('first_name', 'last_name',)
    fieldsets = (
        (None, {
            'fields': (
                'first_name',
                'last_name',
                'nickname',
                'grade_level',
            )
        }),
    )


@admin.register(Course)
class CourseAdmin(ImportExportActionModelAdmin):
    formats = ACCEPTED_FILE_FORMATS
    resource_class = CourseResource
    preserve_filters = True
    actions = [export_class_roster, ]
    filter_horizontal = ('students', )
    list_display = ('name', 'grade_level', 'owner', 'modified',)
    list_filter = ('grade_level', 'owner', )
    raw_id_fields = ('owner', )
    search_fields = ('name', )
    ordering = ('name',)
    fieldsets = (
        (None, {
            'fields': (
                'name',
                'grade_level',
                'owner',
                'students',
            )
        }),
    )


@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    pass


@admin.register(StudentGrouping)
class StudentGroupingAdmin(admin.ModelAdmin):
    pass


class ObservationAdminForm(forms.ModelForm):

    class Meta:
        model = Observation
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        student_qs = Student.objects
        construct_sublevel_qs = LearningConstructSublevel.objects

        if self.instance.course:
            student_qs = self.instance.course.students

        if self.instance.construct_choices:
            construct_sublevel_qs = LearningConstructSublevel.objects.filter(id__in=self.instance.construct_choices)

        self.fields['students'].queryset = student_qs
        self.fields['constructs'].queryset = construct_sublevel_qs


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    form = ObservationAdminForm
    preserve_filters = True
    filter_horizontal = ('students', 'constructs', 'tags', )
    list_display = ('name', 'owner', 'course', 'created',)
    list_filter = ('course', 'owner',)
    raw_id_fields = ('owner', 'course', 'parent', 'grouping', )
    search_fields = ('name', 'notes')
    ordering = ('name',)
    fieldsets = (
        (None, {
            'fields': (
                'name',
                'original_image',
                'video',
                'students',
                'constructs',
                'tags',
                'parent',
            )
        }),
        ('Notes', {
           'fields': (
               'notes',
               'video_notes',
           )
        }),
        ('Setup Values', {
            'fields': (
                'owner',
                'course',
                'grouping',
                'construct_choices',
                'parent',
            )
        })
    )


@admin.register(LearningConstruct)
class LearningConstructAdmin(admin.ModelAdmin):
    pass


@admin.register(LearningConstructLevel)
class LearningConstructLevelAdmin(admin.ModelAdmin):
    list_display = (
        'get_construct_abbv',
        'level',
        'description',
    )
    list_select_related = ('construct',)

    def get_construct_abbv(self, obj):
        return obj.construct.abbreviation


@admin.register(LearningConstructSublevel)
class LearningConstructSublevelAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description',
    )
    list_filter = (
        'level__construct__abbreviation',
        'level__level',
    )


@admin.register(LearningConstructSublevelExample)
class LearningConstructSublevelExampleAdmin(admin.ModelAdmin):
    list_display = (
        'get_sublevel_name',
        'text',
    )
    list_filter = (
        'sublevel__level__construct__abbreviation',
        'sublevel__level__level',
    )

    def get_sublevel_name(self, obj):
        return obj.sublevel.name
