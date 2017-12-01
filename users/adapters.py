from allauth.account.adapter import DefaultAccountAdapter
from django.http import HttpResponseRedirect
from django.urls import reverse


class PendingUserAccountAdapter(DefaultAccountAdapter):
    """
    This subclass of DefaultAccountAdapter lets us specify a different page than "inactive" when a user is simply
    pending staff approval. This is better than adding a mixin on every single view.
    """

    def respond_user_inactive(self, request, user):
        if user.is_pending:
            return HttpResponseRedirect(reverse('account_pending'))
        else:
            return HttpResponseRedirect(reverse('account_inactive'))
