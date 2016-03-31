"""
Provides a set of pluggable permission policies.
"""

import inspect

from abc import ABCMeta, abstractmethod
from flask import request
from .exceptions import NotAuthenticated, PermissionDenied
from .filters import authorization_filter


@authorization_filter
def authorizer(*permissions):
    permissions = [item() if inspect.isclass(item) else item for item in permissions]

    def authorize():
        for permission in permissions:
            if not permission.has_permission():
                if getattr(request, 'user', None):
                    raise PermissionDenied()
                else:
                    raise NotAuthenticated()

    return authorize


class BasePermission(metaclass=ABCMeta):
    """
    A base class from which all permission classes should inherit.
    """

    @abstractmethod
    def has_permission(self):
        """
        Returns `True` if permission is granted, `False` otherwise.
        """


class AllowAny(BasePermission):
    """
    Allow any access.
    This isn't strictly required, since you could use an empty
    permission_classes list, but it's useful because it makes the intention
    more explicit.
    """

    def has_permission(self):
        return True


class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self):
        return getattr(request, 'user', None) is not None
