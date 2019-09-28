from allauth.account.views import PasswordResetView

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic import ListView, RedirectView

from .forms import CustomPasswordResetForm
from .models import User


class ApproveUserView(PermissionRequiredMixin, RedirectView):
    permission_required = 'kidviz.can_approve_deny_users'

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('id')
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise Http404('User does not exist')
        user.is_pending = False
        user.is_active = True
        user.save()
        messages.success(request, 'User Approved')
        self.url = request.GET.get('redirect')
        return super().get(request, *args, **kwargs)


class DenyUserView(PermissionRequiredMixin, RedirectView):
    permission_required = 'kidviz.can_approve_deny_users'

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('id')
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise Http404('User does not exist')
        user.is_pending = False
        user.is_active = False
        user.save()
        messages.success(request, 'User Denied')
        self.url = request.GET.get('redirect')
        return super().get(request, *args, **kwargs)


class PendingUserListView(PermissionRequiredMixin, ListView):
    permission_required = 'kidviz.can_approve_deny_users'

    model = User
    queryset = User.objects.filter(is_pending=True)
    actions = [('approve_user', 'Approve'), ('deny_user', 'Deny')]


class ApprovedUserListView(PermissionRequiredMixin, ListView):
    permission_required = 'kidviz.can_approve_deny_users'

    model = User
    queryset = User.objects.filter(is_pending=False, is_active=True)
    actions = [('deny_user', 'Deny')]


class DeniedUserListView(PermissionRequiredMixin, ListView):
    permission_required = 'kidviz.can_approve_deny_users'

    model = User
    queryset = User.objects.filter(is_pending=False, is_active=False)
    actions = [('approve_user', 'Approve')]


class CreateNewUser(PermissionRequiredMixin, PasswordResetView):
    permission_required = 'kidviz.can_approve_deny_users'
    form_class = CustomPasswordResetForm
    template_name = 'account/new_user.html'

    def form_valid(self, form):
        email = form.cleaned_data['email']

        user = User(email=email)
        user.set_unusable_password()
        user.save()

        return super().form_valid(form)
