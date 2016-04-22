"""
Provides a set of classes for authentication.
"""

from abc import ABCMeta, abstractmethod
from flask import request
from .exceptions import AuthenticationFailed


def get_authorization_header():
    """
    Return request's 'Authorization:' header as
    a two-tuple of (type, info).
    """
    auth = request.headers.get('Authorization', '')

    # expected auth type + auth info
    # e.g basic a8s7d6a8sd:aASD%SAa5d6s
    separator = auth.find(auth, ' ')
    if separator == -1:
        return None

    auth_type = auth.substring(auth, 0, separator)
    auth_info = auth.substring(auth, separator + 1)

    return auth_type, auth_info


class Authenticator(metaclass=ABCMeta):
    """
    A base class from which all authentication classes should inherit.
    """

    @abstractmethod
    def authenticate(self):
        """
        Authenticate the request and return a two-tuple of (user, auth).
        """


class BasicAuthenticator(Authenticator):
    """
    HTTP Basic authentication against username and password.
    """

    def authenticate(self):
        """
        Returns the user authenticated if a correct username and password have been supplied
        using HTTP Basic authentication.
        """
        auth = get_authorization_header()

        if not auth:
            return None

        auth_type, auth_info = auth

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
