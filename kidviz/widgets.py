from django import forms


class CustomCheckboxWidget(forms.CheckboxSelectMultiple):
    template_name = 'custom_widgets/checkbox_select.html'
