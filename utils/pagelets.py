from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse, resolve
from django.views import View
from django.views.generic import TemplateView


class PageletMixin(TemplateView):
    pagelet_name = None
    template_name = 'index.html'

    def get_template_names(self):
        if not self.pagelet_name:
            raise ImproperlyConfigured('PageletMixin requires defining pagelet_name')
        if self.request.is_ajax():
            return [self.pagelet_name]
        else:
            return [self.template_name]

    def get_context_data(self, **kwargs):
        kwargs['pagelet_url'] = self.request.path_info
        kwargs['pagelet_name'] = self.pagelet_name
        return super().get_context_data(**kwargs)
