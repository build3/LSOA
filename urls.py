from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^users/', include('users.urls')),


    # plugins
    url(r'^plugins/tz_detect/', include('tz_detect.urls')),
]
