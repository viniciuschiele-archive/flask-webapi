"""
Provides filters used to inject code into views.
"""


def filter(allow_multiple=True):
    """
    Filter that performs authentication.
    :param bool allow_multiple:
    """
    def wrapper(cls):
        def decorator(*args, **kwargs):
            instance = cls(*args, **kwargs)
            instance.allow_multiple = allow_multiple
            return instance
        return decorator
    return wrapper


class BaseFilter(object):
    def __init__(self, order=-1):
        self.order = order

    def __call__(self, func):
        func.filters = getattr(func, 'filters', [])
        func.filters.append(self)
        return func


class AuthenticationFilter(BaseFilter):
    """
    Filter that performs authentication.
    """
    def authenticate(self, context):
        pass


class AuthorizationFilter(BaseFilter):
    """
    Filter that performs authorization.
    """
    def authorize(self, context):
        pass


class ActionFilter(BaseFilter):
    """
    Filter that performs authorization.
    """
    def pre_action(self, context):
        pass

    def post_action(self, context):
        pass


class ResponseFilter(BaseFilter):
    """
    Filter that performs authorization.
    """
    def pre_response(self, context):
        pass

    def post_response(self, context):
        pass


class ExceptionFilter(BaseFilter):
    """
    Filter that performs authorization.
    """
    def handle_exception(self, context):
        pass

