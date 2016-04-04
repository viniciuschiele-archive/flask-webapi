"""
Provides a BaseView class that is the base of all views in Flask WebAPI.
"""

from abc import ABCMeta, abstractmethod
from flask import current_app
from werkzeug.exceptions import HTTPException
from . import filters
from .exceptions import APIException, NotAcceptable
from .utils import reflect


def exception_handler(context):
    """
    Handles a specific error, by returning an appropriate response.
    :param ActionContext context: The context of the current action.
    :return: A response
    """
    e = context.exception

    if isinstance(e, APIException):
        message = e
    elif isinstance(e, HTTPException):
        message = APIException(e.description)
        message.status_code = e.code
    else:
        debug = current_app.config.get('DEBUG')
        message = APIException(str(e)) if debug else APIException()

    context.result = {'errors': message.denormalize()}
    context.response.status_code = message.status_code


def route(url, endpoint=None, methods=None):
    """
    A decorator that apply a route to the view or action.
    :param str url: The url rule.
    :param str endpoint: The endpoint.
    :param list methods: A list of http methods.
    :return: A function.
    """
    def decorator(func):
        routes = getattr(func, 'routes', None)
        if not routes:
            func.routes = routes = []
        routes.append((url, endpoint, methods))
        return func

    return decorator


class BaseView(metaclass=ABCMeta):
    """
    A base class from which all view classes should inherit.
    """

    @abstractmethod
    def dispatch(self, context):
        """
        Dispatches the incoming request to the particular method.
        :param ActionContext context:
        """


class View(BaseView):
    """
    The default view class that implements authentication, authorization,
    argument parsing, serialization, error handling.
    """

    def dispatch(self, context):
        """
        Dispatches the incoming request to the particular method.
        :param ActionContext context:
        """
        try:
            self._handle_request(context)
        except Exception as e:
            context.exception = e
            self._handle_exception(context)

    def _handle_request(self, context):
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
            self._execute_exception_filters(context)

            if not context.exception_handled:
                raise

            self._make_response_with_filters(context)

    def _handle_exception(self, context):
        """
        Handles any error that occurs, giving the opportunity for
        custom error handling by user code.
        :param Exception e: The exception.
        :return: A `flask.Response` instance.
        """
        context.exception_handler(context)

        self._make_response_with_filters(context, force_formatter=True)

    def _execute_authentication_filters(self, context):
        for filter in context.authentication_filters:
            filter.authenticate(context)

    def _execute_authorization_filters(self, context):
        for filter in context.authorization_filters:
            filter.authorize(context)

    def _execute_action_with_filters(self, context):
        for filter in context.action_filters:
            filter.pre_action(context)

        if context.result is None:
            context.result = context.func(self, *context.args, **context.kwargs)

        for filter in context.action_filters:
            filter.post_action(context)

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

        for filter in context.response_filters:
            filter.post_response(context)

    def _select_output_formatter(self, context, force=False):
        """
        Determines which renderer should be used to render the outgoing response.
        :param force: If set to `True` selects the first renderer when the appropriated is not found.
        :return: A tuple with renderer and the mimetype.
        """
        negotiator = context.content_negotiator
        formatters = context.output_formatters

        try:
            return negotiator.select_output_formatter(formatters)
        except NotAcceptable:
            if not force:
                raise
            return formatters[0], formatters[0].mimetype


class ActionContext(object):
    """
    Represents a func in the View that should be
    treated as a Flask view.
    """

    def __init__(self, func, view_class, api):
        self.func = func
        self.view_class = view_class
        self.api = api
        self.app = api.app

        self.authentication_filters = self.__get_filters_by_type(filters.AuthenticationFilter)
        self.authorization_filters = self.__get_filters_by_type(filters.AuthorizationFilter)
        self.action_filters = self.__get_filters_by_type(filters.ActionFilter)
        self.response_filters = self.__get_filters_by_type(filters.ResponseFilter)
        self.exception_filters = self.__get_filters_by_type(filters.ExceptionFilter)

        self.content_negotiator = api.content_negotiator
        self.exception_handler = api.exception_handler
        self.input_formatters = api.input_formatters
        self.output_formatters = api.output_formatters
        self.value_providers = api.value_providers

        if not reflect.has_self_parameter(self.func):
            self.func = reflect.func_to_method(self.func)

        self.args = None
        self.kwargs = None
        self.result = None
        self.exception = None
        self.exception_handled = False
        self.response = None

    def __get_filters_by_type(self, filter_type):
        filters_by_type = sorted([filter for filter in
                                  getattr(self.func, 'filters', []) +
                                  getattr(self.view_class, 'filters', []) +
                                  getattr(self.api, 'filters', [])
                                  if isinstance(filter, filter_type)], key=lambda x: x.order)

        filters = []

        while len(filters_by_type) > 0:
            filter = filters_by_type.pop(0)
            filters.append(filter)
            if not getattr(filter, 'allow_multiple', True):
                for next_filter in list(filters_by_type):
                    if not isinstance(next_filter, type(filter)):
                        filters_by_type.remove(next_filter)
                        filters.append(next_filter)

        return filters
