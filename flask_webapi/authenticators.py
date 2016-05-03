"""
Provides a set of classes for authentication.
"""

from abc import ABCMeta, abstractmethod
from flask import request


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


class AuthenticateResult:
    """
    Contains the result of an Authenticate call
    """
    def __init__(self):
        self.user = None
        self.auth = None
        self.failure = None
        self.skipped = False
        self.succeeded = False

    @staticmethod
    def fail(message):
        """
        Creates a failed result.
        :param str message: The error message.
        :return: A `AuthenticateResult`.
        """
        result = AuthenticateResult()
        result.failure = message
        return result

    @staticmethod
    def success(user, auth):
        """
        Creates a succeeded result.
        :param user: The user info.
        :param auth: The authentication info.
        :return: A `AuthenticateResult`.
        """
        result = AuthenticateResult()
        result.user = user
        result.auth = auth
        result.succeeded = True
        return result

    @staticmethod
    def skip():
        """
        Creates a skipped result.
        :return: A `AuthenticateResult`.
        """
        result = AuthenticateResult()
        result.skipped = True
        return result


class Authenticator(metaclass=ABCMeta):
    """
    A base class from which all authentication classes should inherit.
    """

    @abstractmethod
    def authenticate(self):
        """
        Authenticate the request and return a `AuthenticateResult`.
        """


class BasicAuthenticator(Authenticator):
    """
    HTTP Basic authentication against username and password.
    """

    def authenticate(self):
        """
        Returns the user authenticated if a correct username and password have been supplied
        using HTTP Basic authentication.
        :return: A `AuthenticateResult`.
        """
        auth = get_authorization_header()

        if not auth:
            return AuthenticateResult.skip()

        auth_type, auth_info = auth

        if auth_type != 'basic':
            return AuthenticateResult.skip()

        try:
            username, password = auth_info.split(':')
        except ValueError:
            return AuthenticateResult.fail('Invalid basic header. Credentials not correctly base64 encoded.')

        return self._authenticate_credentials(username, password)

    def _authenticate_credentials(self, username, password):
        """
        Authenticates the given username and password.
        :param username: The username to be authenticated.
        :param password: The password to be authenticated.
        :return: A `AuthenticateResult`.
        """
        raise NotImplementedError()
