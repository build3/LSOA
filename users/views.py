from allauth.socialaccount.forms import DisconnectForm
from allauth.socialaccount.views import ConnectionsView
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponseNotAllowed
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, RedirectView, UpdateView

from .models import User


@method_decorator(staff_member_required, name='dispatch')
class ApproveUserView(RedirectView):
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


@method_decorator(staff_member_required, name='dispatch')
class DenyUserView(RedirectView):
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


@method_decorator(staff_member_required, name='dispatch')
class PendingUserListView(ListView):
    model = User
    queryset = User.objects.filter(is_pending=True)
    actions = [('approve_user', 'Approve'), ('deny_user', 'Deny')]


@method_decorator(staff_member_required, name='dispatch')
class ApprovedUserListView(ListView):
    model = User
    queryset = User.objects.filter(is_pending=False, is_active=True)
    actions = [('deny_user', 'Deny')]


@method_decorator(staff_member_required, name='dispatch')
class DeniedUserListView(ListView):
    model = User
    queryset = User.objects.filter(is_pending=False, is_active=False)
    actions = [('approve_user', 'Approve')]


class UpdateUserView(UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'email']
    success_url = reverse_lazy('account_edit')

    def get_object(self, **kwargs):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Account updated!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs['connect_form'] = DisconnectForm(request=self.request)
        return super().get_context_data(**kwargs)


class ConnectedAccountsFormView(ConnectionsView):
    success_url = reverse_lazy('account_edit')

    def get(self, request, *args, **kwargs):
        raise HttpResponseNotAllowed('Can only POST to this view')
