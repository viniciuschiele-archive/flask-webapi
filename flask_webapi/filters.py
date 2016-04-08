"""
Provides a set of filter classes used to inject code into actions and views.
"""


def filter(allow_multiple=True):
    """
    Decorator that allows the filter class to be used as a decorator.
    :param bool allow_multiple: Set to `True` to allow multiples
        filter of same type on the same action.
    """
    def wrapper(cls):
        def decorator(*args, **kwargs):
            instance = cls(*args, **kwargs)
            instance.allow_multiple = allow_multiple
            return instance
        return decorator
    return wrapper


class BaseFilter(object):
    """
    A base class from which all filter classes should inherit.
    :param order: The order in which the filter is executed.
    """

    def __init__(self, order=-1):
        self.order = order

    def __call__(self, action):
        """
        Applies the filter on the given action.
        :param action: The action that will receive the filter.
        :return: The action itself.
        """
        action.filters = getattr(action, 'filters', [])
        action.filters.append(self)
        return action


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
    Filter that allows to inject code before and after the action.
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
    Filter that handles unhandled exceptions.
    """
    def handle_exception(self, context):
        pass

