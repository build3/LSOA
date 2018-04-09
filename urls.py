from django.conf.urls import include, url
from django.contrib import admin

import lsoa.setupwizard
import lsoa.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^users/', include('users.urls')),  # TODO are we using this

    # related select AJAX view for setup screen groupings
    url(r'^student_groupings_ajax/$', lsoa.views.GroupingRelatedSelectView.as_view(), name='student-groupings-ajax'),

    url(r'^$', lsoa.views.SetupView.as_view(), name='observation_setup_view'),
    url(r'^observation/$', lsoa.views.ObservationView.as_view(), name='observation_view'),

    # plugins
    url(r'^plugins/tz_detect/', include('tz_detect.urls')),
    url(r'^tinymce/', include('tinymce.urls')),
]
