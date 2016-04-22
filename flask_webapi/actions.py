"""
Provides a set of classes to execution of actions.
"""

import traceback

from abc import ABCMeta, abstractmethod
from flask import current_app
from werkzeug.exceptions import HTTPException
from . import filters
from .exceptions import APIException, NotAcceptable
from .utils import missing, reflect


class ActionContext:
    """
    Represents a func in the View that should be
    treated as a Flask view.

    :param WebAPI api: The Flask WebAPI instance.
    :param ActionDescriptor descriptor: The action descriptor.
    :param tuple args: The list of arguments provided by Flask.
    :param dict kwargs: The dict of arguments provided by Flask.
    """

    def __init__(self, api, descriptor, args, kwargs):
        self.api = api
        self.app = api.app
        self.descriptor = descriptor

        self.content_negotiator = api.content_negotiator
        self.filters = list(descriptor.filters)
        self.input_formatters = list(api.input_formatters)
        self.output_formatters = list(api.output_formatters)
        self.value_providers = dict(api.value_providers)

        self.args = args
        self.kwargs = kwargs
        self.result = missing
        self.exception = None
        self.exception_handled = False
        self.response = self.app.response_class()


class ActionDescriptor:
    """
    Represents an action.
    """
    def __init__(self):
        self.func = None
        self.view_class = None
        self.filters = []


class ActionDescriptorBuilder:
    """
    Creates instances of `ActionDescriptor`.
    """

    def build(self, func, view_class, api):
        """
        Creates a instance of `ActionDescriptor`
        from the given parameters.
        :param func: The function.
        :param view_class: The class which the `func` belongs to.
        :param WebAPI api: The Flask WebAPI.
        :return: The instance of `ActionDescriptor`.
        """
        if not reflect.has_self_parameter(func):
            func = reflect.func_to_method(func)

        descriptor = ActionDescriptor()
        descriptor.func = func
        descriptor.view_class = view_class

        descriptor.filters = self._get_filters(getattr(func, 'filters', []),
                                               getattr(view_class, 'filters', []),
                                               api.filters)

        return descriptor

    def _get_filters(self, action_filters, view_filters, api_filters):
        """
        Gets a list of filters ordered by order of execution.
        :param action_filters: The filters from action.
        :param view_filters: The filters from view.
        :param api_filters: The filters from `WebAPI`.
        :return: The list of filters.
        """
        filters = sorted(action_filters + view_filters + api_filters, key=lambda x: x.order)

        filter_matched = []

        for filter in filters:
            if filter.allow_multiple or not [f for f in filter_matched if type(f) == type(filter)]:
                filter_matched.insert(0, filter)

        return filter_matched


class ActionExecutor(metaclass=ABCMeta):
    """
    A base class from which all executor classes should inherit.
    """

    @abstractmethod
    def execute(self, context):
        """
        Executes an action.
        :param context:
        """
        pass


class DefaultActionExecutor(ActionExecutor):
    """
    Responsible to execute an action and its filters.
    """

    def execute(self, context):
        """
        Executes an action with all its filters.
        :param context: The action context.
        :return: A `flask.Response` instance.
        """

        try:
            context.cursor = _FilterCursor(context.filters)
            self._execute_authentication_filters(context)

            context.cursor.reset()
            self._execute_authorization_filters(context)

            context.cursor.reset()
            self._execute_resource_filters(context)
        except Exception as e:
            context.exception = e
            self._handle_exception(context)

    def _handle_exception(self, context):
        """
        Handles any unhandled error that occurs
        and creates a proper response for it.
        :param ActionContext context: The action context.
        """
        if isinstance(context.exception, APIException):
            message = context.exception
        elif isinstance(context.exception, HTTPException):
            message = APIException(context.exception.description)
            message.status_code = context.exception.code
        else:
            debug = current_app.config.get('DEBUG')
            message = APIException(traceback.format_exc()) if debug else APIException()
            context.app.logger.error(traceback.format_exc())

        context.result = {'errors': message.denormalize()}
        context.response.status_code = message.status_code

        self._make_response(context, force_formatter=True)

    def _execute_authentication_filters(self, context):
        """
        Executes all authentication filters for the given action.
        :param context: The action context.
        """
        cursor = context.cursor

        filter = cursor.get_next(filters.AuthenticationFilter)

        if filter:
            filter.on_authentication(context)
            self._execute_authentication_filters(context)

    def _execute_authorization_filters(self, context):
        """
        Executes all authorization filters for the given action.
        :param context: The action context.
        """
        cursor = context.cursor

        filter = cursor.get_next(filters.AuthorizationFilter)

        if filter:
            filter.on_authorization(context)
            self._execute_authorization_filters(context)

    def _execute_resource_filters(self, context):
        """
        Executes all resource filters for the given action.
        :param context: The action context.
        """
        cursor = context.cursor

        if context.result is not missing:
            self._make_response(context)
            return

        filter = cursor.get_next(filters.ResourceFilter)

        if filter:
            filter.on_resource_execution(context, self._execute_resource_filters)
        else:
            cursor.reset()

            # >> ExceptionFilters >> ActionFilters >> Action
            self._execute_exception_filters(context)

            if context.exception and not context.exception_handled:
                raise context.exception

            cursor.reset()
            self._execute_response_filters(context)

    def _execute_exception_filters(self, context):
        """
        Executes all exception filters for the given action.
        :param context: The action context.
        """
        cursor = context.cursor

        if context.result is not missing:
            return

        filter = cursor.get_next(filters.ExceptionFilter)

        if filter:
            self._execute_exception_filters(context)

            if context.exception and not context.exception_handled:
                filter.on_exception(context)
        else:
            cursor.reset()

            try:
                self._execute_action_filters(context)
            except Exception as e:
                context.exception = e

    def _execute_action_filters(self, context):
        """
        Executes all action filters for the given action.
        :param context: The action context.
        """
        cursor = context.cursor

        if context.result is not missing:
            return

        filter = cursor.get_next(filters.ActionFilter)

        if filter:
            filter.on_action_execution(context, self._execute_action_filters)
        else:
            view = context.descriptor.view_class()
            context.result = context.descriptor.func(view, *context.args, **context.kwargs)

    def _execute_response_filters(self, context):
        """
        Executes all response filters for the given action.
        :param context: The action context.
        """
        cursor = context.cursor

        filter = cursor.get_next(filters.ResponseFilter)

        if filter:
            filter.on_response(context, self._execute_response_filters)
        else:
            self._make_response(context)

    def _make_response(self, context, force_formatter=False):
        """
        Returns a `flask.Response` for the given data.
        The appropriated renderer is taken based on the request header Accept.
        If there is not data to be serialized the response status code is 204.

        :param context: The Python object to be serialized.
        :param bool force_formatter: If set to `True` selects the first formatter when the appropriated is not found.
        :return: A Flask response.
        """
        if context.response is context.app.response_class:
            return

        if context.result is None:
            context.response.status_code = 204
        else:
            formatter, mimetype = self._select_output_formatter(context, force_formatter)
            formatter.write(context.response, context.result, mimetype)

    def _select_output_formatter(self, context, force=False):
        """
        Determines which formatter should be used to render the outgoing response.
        :param force: If set to `True` selects the first formatter when the appropriated is not found.
        :return: A tuple with renderer and the mimetype.
        """
        negotiator = context.content_negotiator
        formatters = context.output_formatters

        formatter_pair = negotiator.select_output_formatter(formatters)

        if formatter_pair:
            return formatter_pair

        if force:
            return formatters[0], formatters[0].mimetype

        raise NotAcceptable()


class _FilterCursor:
    """
    Internal class to move across the filters.
    """
    def __init__(self, filters):
        self._index = 0
        self._filters = filters

    def get_next(self, filter_type):
        while self._index < len(self._filters):
            filter = self._filters[self._index]

            self._index += 1

            if isinstance(filter, filter_type):
                return filter

        return None

    def reset(self):
        self._index = 0
