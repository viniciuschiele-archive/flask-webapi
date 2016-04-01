"""
Provides a BaseView class that is the base of all views in Flask WebAPI.
"""

from abc import ABCMeta, abstractmethod
from flask import current_app
from werkzeug.exceptions import HTTPException
from .exceptions import APIException, NotAcceptable
from .filters import authentication_filter, authorization_filter, action_filter, response_filter, exception_filter
from .utils import reflect


def exception_handler(context):
    """
    Handles a specific error, by returning an appropriate response.
    :param BaseView view: The view which raised the exception.
    :param Exception e: The exception.
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
        for filter in context.authentication_filters:
            filter.authenticate(context)

        for filter in context.authorization_filters:
            filter.authorize(context)

        try:
            for filter in context.action_filters:
                filter.before_action(context)

            if context.result is None:
                context.result = context.func(self, *context.args, **context.kwargs)

            for filter in context.action_filters:
                filter.after_action(context)
        except Exception as e:
            context.exception = e
            for filter in context.exception_filters:
                filter.on_exception(context)

            if context.result is None:
                raise
        else:
            for filter in context.response_filters:
                filter.before_response(context)

        self._make_response(context)

        for filter in context.response_filters:
            filter.after_response(context)

    def _handle_exception(self, context):
        """
        Handles any error that occurs, giving the opportunity for
        custom error handling by user code.
        :param Exception e: The exception.
        :return: A `flask.Response` instance.
        """
        context.exception_handler(context)

        self._make_response(context, force_renderer=True)

    def _make_response(self, context, force_renderer=False):
        """
        Returns a `flask.Response` for the given data.
        The appropriated renderer is taken based on the request header Accept.
        If there is not data to be serialized the response status code is 204.

        :param context: The Python object to be serialized.
        :param bool force_renderer: If set to `True` selects the first renderer when the appropriated is not found.
        :return: A Flask response.
        """
        result = context.result
        if result is None:
            context.response.status_code = 204
            return

        if type(context.response) == type(result):
            context.response = result

        renderer, mimetype = self._select_renderer(context, force_renderer)
        response_bytes = renderer.render(result, mimetype)
        context.response.content_type = str(mimetype)
        context.response.set_data(response_bytes)

    def _select_renderer(self, context, force=False):
        """
        Determines which renderer should be used to render the outgoing response.
        :param force: If set to `True` selects the first renderer when the appropriated is not found.
        :return: A tuple with renderer and the mimetype.
        """
        negotiator = context.content_negotiator
        renderers = context.renderers

        try:
            return negotiator.select_renderer(renderers)
        except NotAcceptable:
            if not force:
                raise
            return renderers[0], renderers[0].mimetype


class ActionContext(object):
    """
    Represents a func in the View that should be
    treated as a Flask view.
    """

    def __init__(self, func, view, api):
        self.func = func
        self.view = view
        self.api = api
        self.app = api.app

        self.authentication_filters = self.__get_filters_by_type(authentication_filter)
        self.authorization_filters = self.__get_filters_by_type(authorization_filter)
        self.action_filters = self.__get_filters_by_type(action_filter)
        self.response_filters = self.__get_filters_by_type(response_filter)
        self.exception_filters = self.__get_filters_by_type(exception_filter)

        self.argument_providers = api.argument_providers
        self.content_negotiator = self.api.content_negotiator
        self.parsers = self.api.parsers
        self.renderers = self.api.renderers
        self.exception_handler = api.exception_handler

        if not reflect.has_self_argument(self.func):
            self.func = reflect.func_to_method(self.func)

        self.args = None
        self.kwargs = None
        self.result = None
        self.exception = None
        self.response = None

    def __get_filters_by_type(self, filter_type):
        filters = getattr(self.func, 'filters', []) + \
                  getattr(self.view, 'filters', []) + \
                  getattr(self.api, 'filters', [])

        return sorted([filter for filter in filters if isinstance(filter, filter_type)], key=lambda x: x.order)
