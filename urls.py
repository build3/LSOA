from django.conf.urls import include, url
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

import settings
import kidviz.views

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='/setup/'), name='index'),

    # setup view is the first view you see after logging in
    url(r'^setup/$', kidviz.views.SetupView.as_view(), name='setup'),
    url(r'^setup-dump/$', kidviz.views.SetupView.as_view(), name='setup_dump'),
    url(r'^setup-groupings-ajax/$', kidviz.views.GroupingRelatedSelectView.as_view(), name='student-groupings-ajax'),
    url(r'^setup/course-default-ajax$', kidviz.views.DefaultCourseView.as_view(), name='set-default-course'),

    # "New Group" screen
    url(r'^grouping/$', kidviz.views.GroupingView.as_view(), name='grouping'),
    url(r'^grouping/save/$', kidviz.views.GroupingSubmitView.as_view(), name='grouping_save'),

    # past observations view shows the "star charts"
    url(r'^observations/$', kidviz.views.ObservationAdminView.as_view(), name='observations_all'),
    url(r'^observations-ajax/$', kidviz.views.ObservationAjax.as_view(), name='observations-ajax'),
    url(r'^observations-teachers/$', kidviz.views.TeacherObservationView.as_view(), name='observations_teachers'),
    url(r'^observations-teachers/(?P<course_id>\d+)/$', kidviz.views.TeacherObservationView.as_view(),
        name='observations_teachers_specific'),
    url(r'^observations-work-queue/$', kidviz.views.WorkQueue.as_view(), name='work-queue'),
    url(r'^observations-remove-draft/(?P<pk>\d+)/$', kidviz.views.RemoveDraft.as_view(), name='remove-draft'),
    url(r'^observation-new/$', kidviz.views.StartNewObservation.as_view(), name='new-observation'),
    url(r'^observation-new/students-timeline/$', kidviz.views.StudentsTimelineView.as_view(), name='students-timeline'),

    # pending/approved/denied users (for admins only)
    url(r'^users/', include('users.urls')),

    # admin site - used to allow teachers to create/modify their classes
    url(r'^admin/', admin.site.urls),

    # observation view - the main screen of the application
    url(r'^observation/$', kidviz.views.ObservationCreateView.as_view(), name='observation_view'),
    url(r'^observation/(?P<pk>\d+)/$', kidviz.views.ObservationDetailView.as_view(), name='observation_detail_view'),
    url(r'^observation/dismiss-draft/$', kidviz.views.DismissDraft.as_view(), name='dismiss_draft'),
    url(r'^current-observation/$', kidviz.views.current_observation, name='current_observation'),

    # tag management
    url(r'^tag/$', kidviz.views.CreateTag.as_view(), name='create_tag'),
    url(r'^tag/(?P<pk>\d+)/$', kidviz.views.EditTag.as_view(), name='edit_tag'),
    url(r'^tag/list/$', kidviz.views.ListTag.as_view(), name='tag_list'),

    # plugins
    url(r'^plugins/tz_detect/', include('tz_detect.urls')),
    url(r'^tinymce/', include('tinymce.urls')),

    # data imports
    path('class-roster/import/', kidviz.views.ImportClassRoster.as_view(), name='import_class_roster'),
    path('class-roster/process-import/', kidviz.views.process_class_roster, name='process_import_class_roster'),
    path('class-roster/export/', kidviz.views.export_class_roster, name='export_class_roster'),

    # reports
    path('report/floating', kidviz.views.FloatingStudents.as_view(), name='floating_students'),
    path('report/doubled', kidviz.views.DoubledStudents.as_view(), name='doubled_students'),
    path('report/homonym', kidviz.views.HomonymStudents.as_view(), name='homonym_students'),
    path('report/ajax', kidviz.views.StudentReportAjax.as_view(), name='report_ajax'),

]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
