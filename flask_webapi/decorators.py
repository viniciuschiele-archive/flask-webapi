"""
Provides a set of decorator.
"""

from . import filters


def route(url, endpoint=None, methods=None):
    """
    A decorator that apply a route to the view or action.
    :param str url: The url rule.
    :param str endpoint: The endpoint.
    :param list methods: A list of http methods.
    :return: A function.
    """
    if not url:
        raise ValueError('url cannot be empty.')

    def decorator(func):
        routes = getattr(func, 'routes', None)
        if not routes:
            func.routes = routes = []
        routes.append((url, endpoint, methods))
        return func

    return decorator


# aliases to be used as decorators
allow_anonymous = filters.AllowAnonymous
authenticate = filters.AuthenticateFilter
authorize = filters.AuthorizeFilter
compat = filters.CompatFilter
consume = filters.ConsumeFilter
produce = filters.ProduceFilter
param = filters.ParameterFilter
serialize = filters.SerializeFilter
