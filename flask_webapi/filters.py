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
    A filter that surrounds execution of the authentication.
    """
    def on_authentication(self, context):
        pass


class AuthorizationFilter(Filter):
    """
    A filter that surrounds execution of the authorization.
    """
    def on_authorization(self, context):
        pass


class ResourceFilter(Filter):
    """
    A filter that surrounds execution of the action (and filters) and the response (and filters).
    """
    def on_resource_execution(self, context, next_filter):
        pass


class ExceptionFilter(Filter):
    """
    A filter that runs after an action has thrown an exception.
    """
    def on_exception(self, context):
        pass


class ActionFilter(Filter):
    """
    A filter that surrounds execution of the action.
    """
    def on_action_execution(self, context, next_filter):
        pass


class ResponseFilter(Filter):
    """
    A filter that surrounds creation of the response.
    """
    def on_response_creation(self, context, next_filter):
        pass
