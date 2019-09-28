from allauth.account.adapter import get_adapter
from allauth.account.forms import ResetPasswordForm

from django import forms
from django.contrib.auth.models import Group

from .models import User


class SignupForm(forms.Form):
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)

    def signup(self, request, user):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        teachers = Group.objects.get(name='Teachers')
        teachers.user_set.add(user)


class CustomPasswordResetForm(ResetPasswordForm):
    def clean_email(self):
        email = self.cleaned_data["email"]
        email = get_adapter().clean_email(email)

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('User with {} already exists'.format(email))

        self.users = User.objects.filter(email=email)

        return self.cleaned_data["email"]
