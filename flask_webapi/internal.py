import traceback

from flask import current_app, request
from flask_webapi.utils.mimetypes import MimeType
from werkzeug.exceptions import HTTPException
from . import filters, results, status
from .exceptions import APIException
from .utils import collections, reflect


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

        self.object_result_factory = api.object_result_factory
        self.object_result_executor = api.object_result_executor

        self.filters = list(descriptor.filters)
        self.input_formatters = list(api.input_formatters)
        self.output_formatters = list(api.output_formatters)
        self.value_providers = dict(api.value_providers)

        self.args = args
        self.kwargs = kwargs
        self.result = None
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


class ActionExecutor:
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

        result = results.ObjectResult({'errors': message.denormalize()}, status_code=message.status_code)
        result.execute(context)

    def _execute_authentication_filters(self, context):
        """
        Executes all authentication filters for the given action.
        :param context: The action context.
        """
        if context.result is not None:
            self._execute_action_result(context)
            return

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
        if context.result is not None:
            self._execute_action_result(context)
            return

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
        if context.result is not None:
            self._execute_action_result(context)
            return

        cursor = context.cursor

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
            self._execute_result_filters(context)

    def _execute_exception_filters(self, context):
        """
        Executes all exception filters for the given action.
        :param context: The action context.
        """
        if context.result is not None:
            return

        cursor = context.cursor

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
        if context.result is not None:
            return

        cursor = context.cursor

        filter = cursor.get_next(filters.ActionFilter)

        if filter:
            filter.on_action_execution(context, self._execute_action_filters)
        else:
            descriptor = context.descriptor
            view = descriptor.view_class()
            result = descriptor.func(view, *context.args, **context.kwargs)

            if isinstance(result, context.app.response_class):
                context.response = result
            elif isinstance(result, results.ActionResult):
                context.result = result
            else:
                object_result_factory = context.object_result_factory
                context.result = object_result_factory.create(result, context)

    def _execute_result_filters(self, context):
        """
        Executes all result filters for the given action.
        :param context: The action context.
        """
        if context.result is None:
            return

        cursor = context.cursor

        filter = cursor.get_next(filters.ResultFilter)

        if filter:
            filter.on_result_execution(context, self._execute_result_filters)
        else:
            self._execute_action_result(context)

    def _execute_action_result(self, context):
        context.result.execute(context)


class ObjectResultExecutor:
    def execute(self, context, result):
        value = result.value

        if result.status_code is None:
            context.response.status_code = 204 if value is None else 200
        else:
            context.response.status_code = result.status_code

        if value is None:
            return

        if result.schema:
            if collections.is_collection(value):
                value = result.schema.dumps(value)
            else:
                value = result.schema.dump(value)

        formatter_pair = self._select_output_formatter(context)

        if formatter_pair is None:
            context.response.status_code = status.HTTP_406_NOT_ACCEPTABLE
        else:
            formatter, mimetype = formatter_pair
            formatter.write(context.response, value, mimetype)

    def _select_output_formatter(self, context, force=False):
        """
        Selects the appropriated formatter that matches to the request accept header.
        :param context: The action context.
        :param force: If set to `True` selects the first formatter when the appropriated is not found.
        :return: A tuple with renderer and the mimetype.
        """
        formatters = context.output_formatters

        for mimetype in self._get_accept_list():
            accept_mimetype = MimeType.parse(mimetype)
            for formatter in formatters:
                if accept_mimetype.match(formatter.mimetype):
                    return formatter, formatter.mimetype.replace(params=accept_mimetype.params)

        if force:
            return formatters[0], formatters[0].mimetype

        return None

    def _get_accept_list(self):
        """
        Given the incoming request, return a list of accepted media type strings.
        """
        header = request.environ.get('HTTP_ACCEPT') or '*/*'
        return [token.strip() for token in header.split(',')]


class ObjectResultFactory:
    def create(self, value, context):
        object_result_filter = None

        for f in context.filters:
            if isinstance(f, filters.ObjectResultFilter):
                object_result_filter = f
                break

        schema = None
        status_code = None

        if object_result_filter:
            schema = object_result_filter.schema
            status_code = object_result_filter.status_code

        return results.ObjectResult(value, schema=schema, status_code=status_code)


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
