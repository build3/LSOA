from django.conf.urls import include, url
from django.views.generic import TemplateView

from users.views import ApproveUserView, ApprovedUserListView, DeniedUserListView, DenyUserView, PendingUserListView, \
    UpdateUserView, ConnectedAccountsFormView

urlpatterns = [
    url(r'^pending/$', PendingUserListView.as_view(), name='pending_users'),
    url(r'^approved/$', ApprovedUserListView.as_view(), name='approved_users'),
    url(r'^denied/$', DeniedUserListView.as_view(), name='denied_users'),

    url(r'^(?P<id>[0-9]+)/approve/$',
        ApproveUserView.as_view(), name='approve_user'),
    url(r'^(?P<id>[0-9]+)/deny/$', DenyUserView.as_view(), name='deny_user'),
    url(r'^accounts/', include('allauth.urls')),
    url(r"^accounts/pending/$", TemplateView.as_view(template_name='account/account_pending.html'),
        name="account_pending"),
    url(r'^accounts/edit/$', UpdateUserView.as_view(), name='account_edit'),
    url(r'^accounts/update_connections/$', ConnectedAccountsFormView.as_view(), name='account_update_connections'),
]
