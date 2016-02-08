"""
Provides a set of pluggable permission policies.
"""

from abc import ABCMeta, abstractmethod
from flask import request


class PermissionBase(metaclass=ABCMeta):
    """
    A base class from which all permission classes should inherit.
    """

    @abstractmethod
    def has_permission(self):
        """
        Return `True` if permission is granted, `False` otherwise.
        """


class IsAuthenticated(PermissionBase):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self):
        return hasattr(request, 'user') and request.user is not None
