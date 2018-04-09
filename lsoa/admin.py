from django.contrib import admin

from .models import Course, LearningConstruct, LearningConstructLevel, LearningConstructSublevel, \
    LearningConstructSublevelExample, Observation, Student, StudentGroup, StudentGrouping

admin.site.site_header = 'LSOA Settings'
admin.site.site_title = 'LSOA Admin'
admin.site.site_url = '/'
admin.site.index_title = 'Settings'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    pass


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    pass


@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    pass


@admin.register(StudentGrouping)
class StudentGroupingAdmin(admin.ModelAdmin):
    pass


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    pass


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
