from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^users/', include('users.urls')),

    url(r'', login_required(TemplateView.as_view(template_name='f7_index.html'))),
    # plugins
    url(r'^plugins/tz_detect/', include('tz_detect.urls')),
]
