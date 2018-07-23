from django.conf.urls import include, url
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

import lsoa.views

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='/setup/'), name='index'),

    # setup view is the first view you see after logging in
    url(r'^setup/$', lsoa.views.SetupView.as_view(), name='setup'),
    url(r'^setup-groupings-ajax/$', lsoa.views.GroupingRelatedSelectView.as_view(), name='student-groupings-ajax'),

    # "New Group" screen
    url(r'^grouping/$', lsoa.views.GroupingView.as_view(), name='grouping'),
    url(r'^grouping/save/$', lsoa.views.GroupingSubmitView.as_view(), name='grouping_save'),

    # past observations view shows the "star charts"
    url(r'^observations/$', lsoa.views.ObservationAdminView.as_view(), name='observations_all'),
    url(r'^observations/(?P<course_id>\d+)/$', lsoa.views.ObservationAdminView.as_view(),
        name='observations_specific'),

    # pending/approved/denied users (for admins only)
    url(r'^users/', include('users.urls')),

    # admin site - used to allow teachers to create/modify their classes
    url(r'^admin/', admin.site.urls),

    # observation view - the main screen of the application
    url(r'^observation/$', lsoa.views.ObservationCreateView.as_view(), name='observation_view'),
    url(r'^observation/(?P<pk>\d+)/$', lsoa.views.ObservationDetailView.as_view(), name='observation_detail_view'),
    url(r'^current-observation/$', lsoa.views.current_observation, name='current_observation'),

    # plugins
    url(r'^plugins/tz_detect/', include('tz_detect.urls')),
    url(r'^tinymce/', include('tinymce.urls')),

    # data imports
    path('class-roster/import/', lsoa.views.ImportClassRoster.as_view(), name='import_class_roster'),
    path('class-roster/process-import/', lsoa.views.process_class_roster, name='process_import_class_roster'),
    path('class-roster/export/', lsoa.views.export_class_roster, name='export_class_roster')
]
