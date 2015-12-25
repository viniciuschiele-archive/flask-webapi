"""
Provides various authentication policies.
"""

from abc import ABCMeta, abstractmethod
from flask import request


def authenticators(*args):
    def decorator(func):
        func.authenticators = args
        return func
    return decorator


def perform_authentication():
    """
    Perform authentication on the incoming request.
    """

    request.user = None
    request.auth = None

    for authenticator in request.action.get_authenticators():
        auth_tuple = authenticator.authenticate()

        if auth_tuple:
            request.user = auth_tuple[0]
            request.auth = auth_tuple[1]
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
        pass
