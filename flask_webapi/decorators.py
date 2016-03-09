"""
Provides various decorators to set up the views and actions.
"""


def authenticator(*args):
    """
    A decorator that apply a list of authenticators to the view or action.
    :param args: A list of authenticators.
    :return: A function.
    """

    def decorator(func):
        func.authenticators = args
        return func
    return decorator


def permissions(*args):
    """
    A decorator that apply a list of permissions to the view or action.
    :param args: A list of permissions.
    :return: A function.
    """

    def decorator(func):
        func.permissions = args
        return func
    return decorator


def content_negotiator(negotiator):
    """
    A decorator that apply a content negotiator to the view or action.
    :param ContentNegotiatorBase negotiator: A class of content negotiator.
    :return: A function.
    """

    def decorator(func):
        func.content_negotiator = negotiator
        return func
    return decorator


def param(name, field, location=None):
    def decorator(func):
        params = getattr(func, 'params', None)
        if params is None:
            func.params = params = {}

        instance = field() if isinstance(field, type) else field
        instance.bind(name, None)
        params[name] = instance, location
        return func
    return decorator


def renderer(*args):
    """
    A decorator that apply a list of renderers to the view or action.
    :param args: A list of renderers.
    :return: A function.
    """

    def decorator(func):
        func.renderers = args
        return func
    return decorator


def route(url, endpoint=None, methods=None):
    """
    A decorator that apply a route to the view or action.
    :param str url: The url rule.
    :param str endpoint: The endpoint.
    :param list methods: A list of http methods.
    :return: A function.
    """

    def decorator(func):
        routes = getattr(func, 'routes', None)
        if not routes:
            func.routes = routes = []
        routes.append((url, endpoint, methods))
        return func
    return decorator


def serializer(serializer_cls, only=None, many=False, envelope=None):
    """
    A decorator that apply marshalling to the return value from the action.
    :param Serializer serializer_cls: The schema class to be used to serialize the values.
    :param only: The name of the fields to be serialized.
    :param bool many: `True` if ``obj`` is a collection so that the object will be serialized to a list.
    :param str envelope: The key used to envelope the data.
    :return: A function.
    """

    def decorator(func):
        func.serializer = serializer_cls
        func.serializer_kwargs = {'only': only,
                                  'many': many,
                                  'envelope': envelope}
        return func
    return decorator


def exception_handler(handler):
    """
    A decorator that apply error handling to the view or action.
    :param handler: A callable object.
    :return: A function.
    """

    def decorator(func):
        func.error_handler = handler
        return func
    return decorator
