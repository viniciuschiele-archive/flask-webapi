"""
Provides various authentication policies.
"""

from abc import ABCMeta, abstractmethod
from flask import request


def perform_authentication():
    """
    Perform authentication on the incoming request.
    """

    request.user = None
    request.auth = None

    for auth in request.action.get_authenticators():
        auth_tuple = auth.authenticate()

        if auth_tuple:
            request.user = auth_tuple[0]
            request.auth = auth_tuple[1]
            break


class AuthenticatorBase(metaclass=ABCMeta):
    """
    A base class from which all authentication classes should inherit.
    """

    @abstractmethod
    def authenticate(self):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        pass
