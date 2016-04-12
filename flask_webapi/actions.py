import traceback

from abc import ABCMeta, abstractmethod
from flask import current_app
from werkzeug.exceptions import HTTPException
from .exceptions import APIException, NotAcceptable
from .filters import AuthenticationFilter, AuthorizationFilter, ActionFilter, ResponseFilter, ExceptionFilter
from .utils import missing, reflect


class ActionContext(object):
    """
    Represents a func in the View that should be
    treated as a Flask view.
    """

    def __init__(self, descriptor, api, args, kwargs):
        self.descriptor = descriptor
        self.api = api
        self.app = api.app

        self.authentication_filters = list(descriptor.authentication_filters)
        self.authorization_filters = list(descriptor.authorization_filters)
        self.action_filters = list(descriptor.action_filters)
        self.response_filters = list(descriptor.response_filters)
        self.exception_filters = list(descriptor.exception_filters)

        self.content_negotiator = api.content_negotiator
        self.input_formatters = list(api.input_formatters)
        self.output_formatters = list(api.output_formatters)
        self.value_providers = dict(api.value_providers)

        self.args = args
        self.kwargs = kwargs
        self.result = missing
        self.exception = None
        self.exception_handled = False
        self.response = self.app.response_class()


class ActionDescriptor(object):
    def __init__(self):
        self.func = None
        self.view_class = None
        self.authentication_filters = []
        self.authorization_filters = []
        self.action_filters = []
        self.response_filters = []
        self.exception_filters = []


class ActionDescriptorBuilder(object):
    def build(self, func, view_class, api):
        if not reflect.has_self_parameter(func):
            func = reflect.func_to_method(func)

        descriptor = ActionDescriptor()
        descriptor.func = func
        descriptor.view_class = view_class

        self._add_filters(descriptor,
                          getattr(func, 'filters', []),
                          getattr(view_class, 'filters', []),
                          api.filters)

        return descriptor

    def _add_filters(self, descriptor, action_filters, view_filters, api_filters):
        filters = action_filters + view_filters + api_filters

        descriptor.authentication_filters = self._get_filters_by_type(filters, AuthenticationFilter)
        descriptor.authorization_filters = self._get_filters_by_type(filters, AuthorizationFilter)
        descriptor.action_filters = self._get_filters_by_type(filters, ActionFilter)
        descriptor.response_filters = self._get_filters_by_type(filters, ResponseFilter)
        descriptor.exception_filters = self._get_filters_by_type(filters, ExceptionFilter)

    def _get_filters_by_type(self, filters, filter_type):
        filters_by_type = sorted([filter for filter in filters
                                  if isinstance(filter, filter_type)], key=lambda x: x.order)

        ret = []

        while len(filters_by_type) > 0:
            filter = filters_by_type.pop(0)
            ret.append(filter)
            if not getattr(filter, 'allow_multiple', True):
                for next_filter in list(filters_by_type):
                    if not isinstance(next_filter, type(filter)):
                        filters_by_type.remove(next_filter)
                        ret.append(next_filter)

        return ret


class ActionExecutor(metaclass=ABCMeta):
    @abstractmethod
    def execute(self, context):
        pass


class DefaultActionExecutor(ActionExecutor):
    def execute(self, context):
        """
        Applies all steps of the pipeline on the incoming request.
        :param ActionContext context:
        :return: A `flask.Response` instance.
        """
        try:
            self._execute_authentication_filters(context)
            self._execute_authorization_filters(context)
            self._execute_action_with_filters(context)
            self._make_response_with_filters(context)
        except Exception as e:
            context.exception = e
            self._handle_exception(context)

    def _handle_exception(self, context):
        """
        Handles any error that occurs, giving the opportunity for
        custom error handling by user code.
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

        context.result = {'errors': message.denormalize()}
        context.response.status_code = message.status_code

        self._make_response_with_filters(context, force_formatter=True)

    def _execute_authentication_filters(self, context):
        for filter in context.authentication_filters:
            filter.authenticate(context)

    def _execute_authorization_filters(self, context):
        for filter in context.authorization_filters:
            filter.authorize(context)

    def _execute_action_with_filters(self, context):
        try:
            for filter in context.action_filters:
                filter.pre_action(context)

            if context.result is missing:
                view = context.descriptor.view_class()
                context.result = context.descriptor.func(view, *context.args, **context.kwargs)

            for filter in reversed(context.action_filters):
                filter.post_action(context)
        except Exception as e:
            context.exception = e

            self._execute_exception_filters(context)

            if not context.exception_handled:
                raise

    def _execute_exception_filters(self, context):
        for filter in context.exception_filters:
            filter.handle_exception(context)

    def _make_response_with_filters(self, context, force_formatter=False):
        """
        Returns a `flask.Response` for the given data.
        The appropriated renderer is taken based on the request header Accept.
        If there is not data to be serialized the response status code is 204.

        :param context: The Python object to be serialized.
        :param bool force_formatter: If set to `True` selects the first formatter when the appropriated is not found.
        :return: A Flask response.
        """

        if not isinstance(context.result, current_app.response_class):
            for filter in context.response_filters:
                filter.pre_response(context)

            if context.result is None:
                context.response.status_code = 204
            else:
                formatter, mimetype = self._select_output_formatter(context, force_formatter)
                formatter.write(context.response, context.result, mimetype)

        for filter in reversed(context.response_filters):
            filter.post_response(context)

    def _select_output_formatter(self, context, force=False):
        """
        Determines which renderer should be used to render the outgoing response.
        :param force: If set to `True` selects the first renderer when the appropriated is not found.
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
