from django.forms import widgets


class SmartSelect(widgets.Select):
    template_name = 'smartselect.html'
