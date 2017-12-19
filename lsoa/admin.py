from django.contrib import admin

from .models import Course, LearningConstruct, Observation, Student, StudentGroup, StudentGrouping


admin.site.site_header = 'LSOA Settings'
admin.site.site_title = 'LSOA Admin'
admin.site.site_url = None
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
