"""
Provides a set of classes for authentication.
"""

import inspect

from abc import ABCMeta, abstractmethod
from flask import request
from .exceptions import AuthenticationFailed
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
        Authenticate the request and return a two-tuple of (user, auth).
        """


class BasicAuthenticator(BaseAuthenticator):
    """
    HTTP Basic authentication against username and password.
    """

    def authenticate(self):
        """
        Returns the user authenticated if a correct username and password have been supplied
        using HTTP Basic authentication, otherwise returns `None`.
        """
        auth = request.authorization

        if not auth:
            return None

        if auth.type.lower() != 'basic':
            return None

        user_auth = self.authenticate_credentials(auth.username, auth.password)

        if user_auth is None:
            raise AuthenticationFailed('Invalid username/password.')

        return user_auth

    def authenticate_credentials(self, username, password):
        """
        Authenticates the given username and password.
        :param username: The username to be authenticated.
        :param password: The username to be authenticated.
        :return: A two-tuple of (user, auth) or `None`.
        """
        raise NotImplementedError()


authenticate = Authenticate
