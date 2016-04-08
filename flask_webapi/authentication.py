"""
Provides a set of classes for authentication.
"""

import inspect

from abc import ABCMeta, abstractmethod
from flask import request
from .filters import AuthenticationFilter, filter


@filter()
class Authenticate(AuthenticationFilter):
    """
    Specifies the authenticator that validates the credentials for the current user.

    :param list authenticators: The list of `BaseAuthenticator`.
    :param int order: The order in which the filter is executed.
    """
    def __init__(self, *authenticators, order=-1):
        super().__init__(order)
        self.authenticators = [item() if inspect.isclass(item) else item for item in authenticators]

    def authenticate(self, context):
        """
        Authenticates the current user.
        :param ActionContext context: The action context.
        """
        request.user = None
        request.auth = None

        for authenticator in self.authenticators:
            auth_tuple = authenticator.authenticate()

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


authenticate = Authenticate
