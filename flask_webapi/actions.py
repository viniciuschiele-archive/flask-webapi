from flask import request
from . import utils


class APIAction(object):
    def __init__(self, func, view_class, api):
        self.func = func
        self.view_class = view_class
        self.app = api.app
        self.api = api

        self.name = view_class.__name__ + ':' + func.__name__

        self.url = view_class.url or ''
        self.url += getattr(func, 'url', '') or ''

        self.methods = func.methods

        self.authenticators = utils.get_attr_3(func, view_class, api, 'authenticators')
        self.permissions = utils.get_attr_3(func, view_class, api, 'permissions')
        self.content_negotiator = utils.get_attr_3(func, view_class, api, 'content_negotiator')
        self.parsers = utils.get_attr_3(func, view_class, api, 'parsers')
        self.renderers = utils.get_attr_3(func, view_class, api, 'renderers')
        self.serializer = utils.get_attr_2(func, view_class, 'serializer')
        self.envelope = getattr(func, 'envelope', None)

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def as_view(self):
        def view(*args, **kwargs):
            request.action = self
            instance = self.view_class()
            return instance.dispatch(*args, **kwargs)

        return view

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
        Instantiates and returns the list of parsers that this view can use.
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

    def get_serializer(self, only=()):
        """
        Instantiates and returns the list of parsers that this view can use.
        """
        return self.serializer(only=only)
