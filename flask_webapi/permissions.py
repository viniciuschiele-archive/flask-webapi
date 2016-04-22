"""
Provides a set of classes for authorization.
"""

from abc import ABCMeta, abstractmethod
from flask import request


class Permission(metaclass=ABCMeta):
    """
    A base class from which all permission classes should inherit.
    """

    @abstractmethod
    def has_permission(self):
        """
        Returns `True` if permission is granted, `False` otherwise.
        """


class IsAuthenticated(Permission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self):
        return getattr(request, 'user', None) is not None
