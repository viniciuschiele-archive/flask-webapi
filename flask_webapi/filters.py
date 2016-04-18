"""
Provides a set of filter classes used to inject code into actions and views.
"""


class Filter:
    """
    A base class from which all filter classes should inherit.
    :param order: The order in which the filter is executed.
    """

    allow_multiple = True

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


class AuthenticationFilter(Filter):
    """
    Filter that performs authentication.
    """
    def authenticate(self, context):
        pass


class AuthorizationFilter(Filter):
    """
    Filter that performs authorization.
    """
    def authorize(self, context):
        pass


class ActionFilter(Filter):
    """
    Filter that allows to inject code before and after the action.
    """

    def pre_action(self, context):
        pass

    def post_action(self, context):
        pass


class ExceptionFilter(Filter):
    """
    Filter that handles unhandled exceptions.
    """
    def handle_exception(self, context):
        pass


class ResponseFilter(Filter):
    """
    Filter that performs authorization.
    """
    def pre_response(self, context):
        pass

    def post_response(self, context):
        pass
