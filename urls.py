from django.conf.urls import include, url
from django.contrib import admin

import lsoa.setupwizard
import lsoa.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^users/', include('users.urls')),

    url(r'^$', lsoa.setupwizard.SetupWizard.as_view(), name='observation_setup_view'),
    url(r'^observation/$', lsoa.views.ObservationView.as_view(), name='observation_view'),

    # plugins
    url(r'^plugins/tz_detect/', include('tz_detect.urls')),
]
