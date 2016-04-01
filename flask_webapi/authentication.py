"""
Provides various authentication policies.
"""

import inspect

from abc import ABCMeta, abstractmethod
from flask import request
from .filters import authentication_filter


class authenticator(authentication_filter):
    def __init__(self, *authenticators, **kwargs):
        super().__init__(**kwargs)
        self.authenticators = [item() if inspect.isclass(item) else item for item in authenticators]

    def authenticate(self, context):
        request.user = None
        request.auth = None

        for auth in self.authenticators:
            auth_tuple = auth.authenticate()

            if auth_tuple:
                request.user, request.auth = auth_tuple
                break


class BaseAuthenticator(metaclass=ABCMeta):
    """
    A base class from which all authentication classes should inherit.
    """

    @abstractmethod
    def authenticate(self):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
