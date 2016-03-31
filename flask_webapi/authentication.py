"""
Provides various authentication policies.
"""

import inspect

from abc import ABCMeta, abstractmethod
from flask import request
from .filters import authentication_filter


@authentication_filter
def authenticator(*authenticators):
    authenticators = [item() if inspect.isclass(item) else item for item in authenticators]

    def authenticate():
        request.user = None
        request.auth = None

        for auth in authenticators:
            auth_tuple = auth.authenticate()

            if auth_tuple:
                request.user, request.auth = auth_tuple
                break

    return authenticate


class BaseAuthenticator(metaclass=ABCMeta):
    """
    A base class from which all authentication classes should inherit.
    """

    @abstractmethod
    def authenticate(self):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
