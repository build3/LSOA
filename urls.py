from django.conf.urls import include, url
from django.contrib import admin

import lsoa.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^users/', include('users.urls')),

    # related select AJAX view for setup screen groupings
    url(r'^student_groupings_ajax/$', lsoa.views.GroupingRelatedSelectView.as_view(), name='student-groupings-ajax'),

    url(r'^$', lsoa.views.SetupView.as_view(), name='observation_setup_view'),
    url(r'^grouping/$', lsoa.views.GroupingView.as_view(), name='grouping_view'),
    url(r'^grouping/save/$', lsoa.views.GroupingSubmitView.as_view(), name='grouping_save'),
    url(r'^observation/$', lsoa.views.ObservationView.as_view(), name='observation_view'),
    url(r'^current-observation/$', lsoa.views.current_observation, name='current_observation'),
    url(r'^a/observations/$', lsoa.views.ObservationAdminView.as_view(), name='observations_all'),
    url(r'^a/observations/(?P<construct_id>\d+)/$', lsoa.views.ObservationAdminView.as_view(),
        name='observations_specific'),

    # plugins
    url(r'^plugins/tz_detect/', include('tz_detect.urls')),
    url(r'^tinymce/', include('tinymce.urls')),
]
