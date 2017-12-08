from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

import lsoa.views


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^users/', include('users.urls')),

    url(r'^$', lsoa.views.default_homepage, name='default_homepage'),
    url(r'class/(?P<course_id>[\d+])/', lsoa.views.view_course, name='view_course'),

    # plugins
    url(r'^plugins/tz_detect/', include('tz_detect.urls')),
]
