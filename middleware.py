from django.utils.deprecation import MiddlewareMixin
from threadlocals.middleware import ThreadLocalMiddleware


class DjangoThreadLocalMiddleware(ThreadLocalMiddleware, MiddlewareMixin):
    pass
