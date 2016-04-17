"""
Provides a set of classes for authentication.
"""

import inspect

from abc import ABCMeta, abstractmethod
from flask import request
from .exceptions import AuthenticationFailed
from .filters import AuthenticationFilter


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


class Authenticator(metaclass=ABCMeta):
    """
    A base class from which all authentication classes should inherit.
    """

    @abstractmethod
    def authenticate(self):
        """
        Authenticate the request and return a two-tuple of (user, auth).
        """


class HttpAuthenticator(Authenticator):
    """
    Base authenticator based on HTTP Authorization header.
    """

    def authenticate(self):
        """
        Returns the user authenticated if a correct Authorization header has been supplied,
        otherwise returns `None`.
        """
        auth = request.headers.get('Authorization', '')

        if not auth:
            return None

        # expected auth type + auth info
        # e.g basic a8s7d6a8sd:aASD%SAa5d6s
        separator = auth.find(auth, ' ')
        if separator == -1:
            return None

        auth_type = auth.substring(auth, 0, separator)
        auth_info = auth.substring(auth, separator + 1)

        return self._authenticate_header(auth_type, auth_info)

    def _authenticate_header(self, auth_type, auth_info):
        """
        Authenticates the given authorization header.
        :param auth_type: The authorization type.
        :param auth_info: The authorization info.
        :return: A two-tuple of (user, auth) or `None`.
        """
        raise NotImplementedError()


class BasicAuthenticator(HttpAuthenticator):
    """
    HTTP Basic authentication against username and password.
    """

    def _authenticate_header(self, auth_type, auth_info):
        """
        Returns the user authenticated if a correct username and password have been supplied
        using HTTP Basic authentication, otherwise returns `None`.
        """
        if auth_type != 'basic':
            return None

        try:
            username, password = auth_info.split(':')
        except ValueError:
            raise AuthenticationFailed('Invalid basic header. Credentials not correctly base64 encoded.')

        user_auth = self._authenticate_credentials(username, password)

        if user_auth is None:
            raise AuthenticationFailed()

        return user_auth

    def _authenticate_credentials(self, username, password):
        """
        Authenticates the given username and password.
        :param username: The username to be authenticated.
        :param password: The password to be authenticated.
        :return: A two-tuple of (user, auth) or `None`.
        """
        raise NotImplementedError()


authenticate = Authenticate
