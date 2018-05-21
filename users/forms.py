from django import forms
from django.contrib.auth.models import Group


class SignupForm(forms.Form):
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)

    def signup(self, request, user):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        teachers = Group.objects.get(name='Teachers')
        teachers.user_set.add(user)
