"""
Provides a set of classes responsible for defining the routing of Python functions for use with Flask
"""

import inspect

from abc import ABCMeta, abstractmethod


def has_routes(obj):
    """
    Checks if the given `obj` has an attribute `routes`.
    :param obj: The obj to be checked.
    :return: True if the `obj` has the attribute.
    """
    return hasattr(obj, 'routes')


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


class Route:
    """
    Represents a route to a Python function.
    """
    def __init__(self, url, endpoint, methods, func, view_class):
        self.url = url
        self.endpoint = endpoint
        self.methods = methods
        self.func = func
        self.view_class = view_class


class BaseRouter(metaclass=ABCMeta):
    """
    A base class from which all router classes should inherit.
    """

    @abstractmethod
    def get_routes(self, view):
        pass


class DefaultRouter(BaseRouter):
    def get_routes(self, view):
        """
        Returns the routes for the given view.
        :param view: The view.
        :return: A list of routes.
        """
        routes = []

        # routes can be set using the decorator
        # @route on top of the class view.
        # e.g:
        #
        # @route('/prefix')
        # class MyView:
        view_routes = self._get_view_routes(view) or ['/']

        for _, func in inspect.getmembers(view):
            action_routes = self._get_action_routes(func)

            # if the action hasn't routes
            # it is ignored.
            if not action_routes:
                continue

            for prefix in view_routes:
                if not prefix.startswith('/'):
                    raise ValueError('url has to start with /')

                for url, endpoint, methods in action_routes:
                    if not url.startswith('/'):
                        raise ValueError('url has to start with /')

                    if not endpoint:
                        endpoint = self._make_endpoint(view, func)

                    routes.append(Route(prefix.rstrip('/') + url, endpoint, methods, func, view))

        return routes

    def _get_view_routes(self, view):
        """
        Returns the routes for the given view.
        :param view: The view.
        :return: A list of `tuple` object.
        """
        return [prefix for prefix, _, _ in getattr(view, 'routes', [])]

    def _get_action_routes(self, func):
        """
        Returns the routes for the given action.
        :param func: The func.
        :return: A list of `tuple` object.
        """
        return getattr(func, 'routes', [])

    def _make_endpoint(self, view, func):
        """
        Returns an endpoint for the given view and func.
        :param BaseView view: The class of your view.
        :param func: The function of your view.
        :return str: The endpoint as string.
        """
        return func.__module__ + '.' + view.__name__ + '.' + func.__name__
