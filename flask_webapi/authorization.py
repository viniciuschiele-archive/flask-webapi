"""
Provides a set of pluggable permission policies.
"""

from abc import ABCMeta, abstractmethod
from flask import request
from .errors import NotAuthenticated, PermissionDenied


def perform_authorization():
    """
    Check if the request should be permitted.
    Raises an appropriate exception if the request is not permitted.
    """

    for permission in request.action.get_permissions():
        if not permission.has_permission():
            if request.user:
                raise PermissionDenied()
            else:
                raise NotAuthenticated()


class PermissionBase(metaclass=ABCMeta):
    """
    A base class from which all permission classes should inherit.
    """

    @abstractmethod
    def has_permission(self):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        pass


class IsAuthenticated(PermissionBase):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self):
        if not hasattr(request, 'user'):
            return False
        return request.user is not None
