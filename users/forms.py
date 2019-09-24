from allauth.account.adapter import get_adapter
from allauth.account.forms import EmailAwarePasswordResetTokenGenerator
from allauth.account.utils import user_pk_to_url_str
from allauth.utils import build_absolute_uri

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import Group
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class SignupForm(forms.Form):
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)

    def signup(self, request, user):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        teachers = Group.objects.get(name='Teachers')
        teachers.user_set.add(user)


class CustomPasswordResetForm(forms.Form):
    ### This is copied from allauth.account.forms. For some reason import is not working.
    ### Only `clean_email` was changed.

    email = forms.EmailField(
        label=_("E-mail"),
        required=True,
        widget=forms.TextInput(attrs={
            "type": "email",
            "size": "30",
            "placeholder": _("E-mail address"),
        })
    )

    def clean_email(self):
        email = self.cleaned_data["email"]
        email = get_adapter().clean_email(email)
        self.users = get_user_model().objects.filter(email=email)

        #if get_user_model().objects.filter(email=email).exists():
            #raise forms.ValidationError('User with {} already exists'.format(email))

        return self.cleaned_data["email"]

    def save(self, request, **kwargs):
        current_site = get_current_site(request)
        email = self.cleaned_data["email"]
        token_generator = EmailAwarePasswordResetTokenGenerator()

        for user in self.users:
            temp_key = token_generator.make_token(user)

            # send the password reset email
            path = reverse("account_reset_password_from_key",
                kwargs=dict(uidb36=user_pk_to_url_str(user), key=temp_key))

            url = build_absolute_uri(request, path)

            context = {
                "current_site": current_site,
                "user": user,
                "password_reset_url": url,
                "request": request
            }

            get_adapter(request).send_mail(
                'account/email/password_reset_key',
                email,
                context
            )

        return self.cleaned_data["email"]
