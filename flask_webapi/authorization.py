"""
Provides a set of pluggable permission policies.
"""

import inspect

from abc import ABCMeta, abstractmethod
from flask import request
from .exceptions import NotAuthenticated, PermissionDenied
from .filters import AuthorizationFilter, filter


@filter()
class authorize(AuthorizationFilter):
    def __init__(self, *permissions, order=-1):
        super().__init__(order)
        self.permissions = [permission() if inspect.isclass(permission) else permission for permission in permissions]

    def authorize(self, context):
        for permission in self.permissions:
            if permission.has_permission():
                return

        if getattr(request, 'user', None):
            raise PermissionDenied()
        else:
            raise NotAuthenticated()


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
