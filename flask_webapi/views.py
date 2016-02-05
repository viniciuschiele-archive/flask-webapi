"""
Provides an ViewVase class that is the base of all views in Flask WebAPI.
"""

import inspect

from .utils import get_attr


class ViewBase(object):
    """
    A base class from which all view classes should inherit.
    """
    pass


class ViewAction(object):
    def __init__(self, func, view, api):
        self.func = func
        self.view = view
        self.api = api

        args = inspect.getargspec(func).args
        self.has_self_param = len(args) > 0 and args[0] == 'self'

        self.url = getattr(view, '_url', None) or ''
        self.url += getattr(func, '_url', None) or ''
        self.allowed_methods = getattr(func, '_methods', None)
        self.authenticators = get_attr((func, view), '_authenticators', api.authenticators)
        self.permissions = get_attr((func, view), '_permissions', api.permissions)
        self.content_negotiator = get_attr((func, view), '_content_negotiator', api.content_negotiator)
        self.parsers = get_attr((func, view), '_parsers', api.parsers)
        self.renderers = get_attr((func, view), '_renderers', api.renderers)
        self.serializer = get_attr((func, view), '_serializer', None)
        self.envelope = getattr(func, '_envelope', None)

    def get_authenticators(self):
        """
        Instantiates and returns the list of authenticators that this view can use.
        """
        return [authenticator() for authenticator in self.authenticators]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        return [permission() for permission in self.permissions]

    def get_content_negotiator(self):
        """
        Instantiates and returns the content negotiator that this action can use.
        """
        return self.content_negotiator()

    def get_parsers(self):
        """
        Instantiates and returns the list of parsers that this view can use.
        """
        return [parser() for parser in self.parsers]

    def get_renderers(self):
        """
        Instantiates and returns the list of renderers that this view can use.
        """
        return [renderer() for renderer in self.renderers]

    def get_serializer(self, fields=()):
        """
        Instantiates and returns the serializer that this action can use.

        :param fields: The name of the fields to be serialized.
        """
        return self.serializer(only=fields)
