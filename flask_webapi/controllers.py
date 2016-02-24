"""
Provides an ControllerBase class that is the base of all controllers in Flask WebAPI.
"""

import inspect

from abc import ABCMeta
from .utils import get_attr


class ControllerBase(metaclass=ABCMeta):
    """
    A base class from which all controller classes should inherit.
    """


class ControllerAction(object):
    def __init__(self, func, controller, api):
        self.func = func
        self.controller = controller
        self.api = api

        args = inspect.getargspec(func).args
        self.has_self_param = len(args) > 0 and args[0] == 'self'

        self.url = getattr(controller, 'url', None) or ''
        self.url += getattr(func, 'url', None) or ''
        self.allowed_methods = getattr(func, 'allowed_methods', None)
        self.authenticators = get_attr((func, controller), 'authenticators', api.authenticators)
        self.permissions = get_attr((func, controller), 'permissions', api.permissions)
        self.content_negotiator = get_attr((func, controller), 'content_negotiator', api.content_negotiator)
        self.parsers = get_attr((func, controller), 'parsers', api.parsers)
        self.renderers = get_attr((func, controller), 'renderers', api.renderers)
        self.serializer = get_attr((func, controller), 'serializer', None)
        self.envelope = getattr(func, 'envelope', None)
        self.error_handler = get_attr((func, controller), 'error_handler', api.error_handler)

    def get_authenticators(self):
        """
        Instantiates and returns the list of authenticators that this controller can use.
        """
        return [authenticator() for authenticator in self.authenticators]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this controller requires.
        """
        return [permission() for permission in self.permissions]

    def get_content_negotiator(self):
        """
        Instantiates and returns the content negotiator that this action can use.
        """
        return self.content_negotiator()

    def get_parsers(self):
        """
        Instantiates and returns the list of parsers that this controller can use.
        """
        return [parser() for parser in self.parsers]

    def get_renderers(self):
        """
        Instantiates and returns the list of renderers that this controller can use.
        """
        return [renderer() for renderer in self.renderers]

    def get_serializer(self, fields=()):
        """
        Instantiates and returns the serializer that this action can use.
        :param fields: The name of the fields to be serialized.
        """
        return self.serializer(only=fields)
