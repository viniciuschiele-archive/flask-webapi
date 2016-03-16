"""
Provides various decorators to set up the views and actions.
"""

import inspect


def authenticator(*args, override=True):
    """
    A decorator that apply a list of authenticators to the view or action.

    :param args: A list of authenticators.
    :param bool override: True to override the authenticators inherited.
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
    :param bool override: True to override the permissions inherited.
    :return: A function.
    """

    def decorator(func):
        func.permissions = [item() if inspect.isclass(item) else item for item in args]
        func.permissions_override = override
        return func
    return decorator


def content_negotiator(negotiator):
    """
    A decorator that apply a content negotiator to the view.

    :param ContentNegotiatorBase negotiator: A class of content negotiator.
    :return: A function.
    """
    def decorator(func):
        func.content_negotiator = negotiator() if inspect.isclass(negotiator) else negotiator
        return func
    return decorator


def parser(*args, override=True):
    """
    A decorator that apply a list of parsers to the view.

    :param args: A list of parsers.
    :param bool override: True to override the parsers inherited.
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
    :param bool override: True to override the renderers inherited.
    :return: A function.
    """

    def decorator(func):
        func.renderers = [item() if inspect.isclass(item) else item for item in args]
        func.renderers_override = override
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


def serializer(cls_or_instance, many=False, envelope=None):
    """
    A decorator that apply marshalling to the return value from the action.
    :param Serializer cls_or_instance: The serializer class used to serialize the values.
    :param bool many: `True` if ``obj`` is a collection so that the object will be serialized to a list.
    :param str envelope: The key used to envelope the data.
    :return: A function.
    """

    def decorator(func):
        func.serializer = cls_or_instance() if inspect.isclass(cls_or_instance) else cls_or_instance
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


def exception_handler(handler):
    """
    A decorator that apply error handling to the view or action.
    :param handler: A callable object.
    :return: A function.
    """

    def decorator(func):
        func.exception_handler = handler
        return func
    return decorator
