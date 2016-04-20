"""
The `compat` module provides support for backwards compatibility with older
versions of Python and Flask.
"""

from flask import request
from .filters import ResourceFilter


class CompatFilter(ResourceFilter):
    """
    A filter that apply a decorator built for Flask.

    >>> from flask.ext.cache import Cache
    >>> cache = Cache(...)

    >>> @route('/users')
    >>> @compat(cache.cached())
    >>> def get_users():

    :param decorator: The decorator.
    :param int order: The order in which the filter is executed.
    """

    def __init__(self, decorator, order=-1):
        super().__init__(order)
        self.decorator = decorator(self._next_filter)

    def on_resource_execution(self, context, next_filter):
        request.compat_filter = (context, next_filter)

        self.decorator(*context.args, **context.kwargs)

    def _next_filter(self, *args, **kwargs):
        context, next_filter = request.compat_filter

        del request.compat_filter

        context.args = args
        context.kwargs = kwargs

        next_filter(context)

        return context.response


compat = CompatFilter  # alias to be used as a decorator
