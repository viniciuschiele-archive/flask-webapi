"""
Provides various decorators to set up the views.
"""

import inspect


def authenticator(*args, override=True):
    """
    A decorator that apply a list of authenticators to the view or action.
    :param args: A list of authenticators.
    :param bool override: If set to `True` the authenticators inherited are overridden.
    :return: A function.
    """
    def decorator(func):
        func.authenticators = [item() if inspect.isclass(item) else item for item in args]
        func.authenticators_override = override
        return func
    return decorator


def permission(*args, override=True):
    """
    A decorator that apply a list of permissions to the view or action.

    :param args: A list of permissions.
    :param bool override: If set to `True` the permissions inherited are overridden.
    :return: A function.
    """

    def decorator(func):
        func.permissions = [item() if inspect.isclass(item) else item for item in args]
        func.permissions_override = override
        return func
    return decorator


def content_negotiator(negotiator):
    """
    A decorator that apply a content negotiator to the view or action.
    :param BaseContentNegotiator negotiator: A class of content negotiator.
    :return: A function.
    """
    def decorator(func):
        func.content_negotiator = negotiator() if inspect.isclass(negotiator) else negotiator
        return func
    return decorator


def parser(*args, override=True):
    """
    A decorator that apply a list of parsers to the view or action.
    :param args: A list of parsers.
    :param bool override: If set to `True` the parsers inherited are overridden.
    :return: A function.
    """
    def decorator(func):
        func.parsers = [item() if inspect.isclass(item) else item for item in args]
        func.parsers_override = override
        return func
    return decorator


def renderer(*args, override=True):
    """
    A decorator that apply a list of renderers to the view or action.
    :param args: A list of renderers.
    :param bool override: If set to `True` the renderers inherited are overridden.
    :return: A function.
    """
    def decorator(func):
        func.renderers = [item() if inspect.isclass(item) else item for item in args]
        func.renderers_override = override
        return func
    return decorator


def param(name, field, location=None):
    """
    A decorator that apply a argument parser to the action.
    :param str name: The name of the parameter.
    :param Field field: The field used to fill the parameter.
    :param str location: Where to retrieve the values.
    :return: A function.
    """
    def decorator(func):
        params = getattr(func, 'params', None)
        if params is None:
            func.params = params = {}

        instance = field() if isinstance(field, type) else field
        instance.bind(name, None)
        params[name] = instance, location
        return func
    return decorator


def serializer(ser, many=None, envelope=None):
    """
    A decorator that apply a serializer to the action.
    :param Serializer ser: The serializer used to serialize the data.
    :param bool many: If set to `True` the object will be serialized to a list.
    :param str envelope: The key used to envelope the data.
    :return: A function.
    """
    def decorator(func):
        func.serializer = ser() if inspect.isclass(ser) else ser
        func.serializer_args = {
            'many': many,
            'envelope': envelope
        }
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

