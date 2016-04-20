"""
Provides a set of classes for authorization.
"""

import inspect

from abc import ABCMeta, abstractmethod
from flask import request
from .exceptions import NotAuthenticated, PermissionDenied
from .filters import AuthorizationFilter


def allow_anonymous(action):
    """
    Allows an action to be called for unauthenticated users.
    :param action: The action to be allowed.
    :return: The action itself.
    """
    action.allow_anonymous = True
    return action


class AuthorizeFilter(AuthorizationFilter):
    """
    Specifies that access to a view or action method is
    restricted to users who meet the authorization requirement.

    :param list permissions: The list of `BasePermission`.
    :param int order: The order in which the filter is executed.
    """
    def __init__(self, *permissions, order=-1):
        super().__init__(order)
        self.permissions = [permission() if inspect.isclass(permission) else permission for permission in permissions]

    def on_authorization(self, context):
        if getattr(context.descriptor.func, 'allow_anonymous', False):
            return

        for permission in self.permissions:
            if permission.has_permission():
                return

        if getattr(request, 'user', None):
            raise PermissionDenied()
        else:
            raise NotAuthenticated()


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


authorize = AuthorizeFilter
