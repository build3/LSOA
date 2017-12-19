from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import RedirectView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import MultipleObjectMixin


class OwnerMixinQuerySet(models.QuerySet):
    """
    Queryset for owner mixin
    """

    def owned_by(self, user, include_staff=False, include_superuser=False):
        """
        Filter by a user(s).

        This method accepts both ``django.contrib.auth.models.User`` instances or user ids.

        :user: user to also filter by.
        :include_staff: any user who has the ``is_staff`` flag does not get filtered.
        :include_superuser: any user who has the ``is_superuser`` flag does not get filtered.
        """
        if not user:
            return []
        UserModel = get_user_model()
        user_pk, user = (user.pk, user) if isinstance(user, UserModel) else (user, None)
        if include_staff or include_superuser:
            if not user:
                user = UserModel.objects.only('is_staff', 'is_superuser').get(pk=user_pk)
            if (include_staff and user.is_staff) or (include_superuser and user.is_superuser):
                return self.all()
        filter_ = {'owner': user_pk}
        return self.filter(**filter_)


class OwnerMixinManager(models.Manager):
    def get_queryset(self):
        return OwnerMixinQuerySet(model=self.model, using=self._db)

    def owned_by(self, user, include_staff=False, include_superuser=False):
        return self.get_queryset().owned_by(user, include_staff=include_staff, include_superuser=include_superuser)


class OwnerMixinBase(models.Model):
    objects = OwnerMixinManager()

    class Meta:
        abstract = True
        default_manager_name = 'objects'

    def is_owned_by(self, user, include_staff=False, include_superuser=False):
        """
        Does this particular user have ownership over this model.

        :user: the user object to check; this can be a ``django.contrib.auth.models.User`` instance
            or a primary key. Recommendation is to pass request.user
        :include_staff: any user who has the ``is_staff`` flag is included as an owner.
        :include_superuser: any user who has the ``is_superuser`` flag is included as an owner.
        :return: True if user has access; else False.
        """
        UserModel = get_user_model()
        # Only touch elements that could cause a database operation if actually needed.
        user_pk, user = (user.pk, user) if isinstance(user, UserModel) else (user, None)
        if include_staff or include_superuser:
            if not user:
                user = UserModel.objects.only('is_staff', 'is_superuser').get(pk=user_pk)
            if (include_staff and user.is_staff) or (include_superuser and user.is_superuser):
                return True
        return user_pk == self.owner_id

    def is_not_owned_by(self, user, include_staff=False, include_superuser=False):
        """
        Convenience method, is an inversion of is_owned_by.
        """
        return not self.is_owned_by(user, include_staff, include_superuser)

    @property
    def is_public(self):
        """
        Public objects have owner set to None
        :return:
        """
        return self.owner == None


class OwnerMixin(OwnerMixinBase):
    owner = models.ForeignKey(get_user_model(), verbose_name=_('owner'), related_name='%(app_label)s_%(class)s_owner')

    class Meta:
        abstract = True


class OptionalOwnerMixin(OwnerMixinBase):
    owner = models.ForeignKey(get_user_model(), verbose_name=_('owner'),
                              related_name='%(app_label)s_%(class)s_owner', null=True, blank=True)

    class Meta:
        abstract = True


class MultipleOwnedObjectViewMixin(LoginRequiredMixin, MultipleObjectMixin, View):
    include_staff = False
    include_superusers = False

    def get_queryset(self):
        return super().get_queryset().owned_by(self.request.user, include_staff=self.include_staff,
                                               include_superuser=self.include_superusers)


class SingleOwnedObjectViewMixin(LoginRequiredMixin, SingleObjectMixin, View):
    """
    Enforces permissions so that users can't access single object pages unless they own them. If
    allow_non_owned is True, items with `owner` == None can be accessed.
    """
    include_staff = False
    include_superusers = False
    allow_non_owned = False

    def get_object(self, queryset=None):
        object = super().get_object(queryset=queryset)
        if object.owner and object.is_owned_by(self.request.user,
                                               include_staff=self.include_staff,
                                               include_superuser=self.include_superusers):
            return object
        elif not object.owner and self.allow_non_owned:
            return object
        raise PermissionDenied()


class OwnerUpdateView(LoginRequiredMixin, UpdateView):
    pass  # Maybe in future, add owner to form fields IF request.user != owner


class OwnerCreateView(LoginRequiredMixin, CreateView):
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class OwnerDeleteView(SingleOwnedObjectViewMixin, RedirectView):
    message = None

    def get(self, request, *args, **kwargs):
        object = self.get_object()
        object.delete()
        if self.message:
            messages.error(request, self.message)
        return super().get(request, *args, **kwargs)


class OwnerActionView(SingleOwnedObjectViewMixin, RedirectView):
    message = None

    def get(self, request, *args, **kwargs):
        self.action(request, *args, **kwargs)
        if self.message:
            messages.info(request, self.message)
        return super().get(request, *args, **kwargs)

    def action(self, request, *args, **kwargs):
        raise NotImplementedError()
