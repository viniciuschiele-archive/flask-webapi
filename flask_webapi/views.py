"""
Provides a BaseView class that is the base of all views in Flask WebAPI.
"""

import copy

from abc import ABCMeta, abstractmethod
from flask import request, current_app
from werkzeug.exceptions import HTTPException
from .exceptions import APIException, NotAcceptable, NotAuthenticated, PermissionDenied, ValidationError
from .filters import authentication_filter, authorization_filter, action_filter, exception_filter
from .schemas import Schema
from .utils import missing, unpack, reflect


def exception_handler(view, e):
    """
    Handles a specific error, by returning an appropriate response.
    :param BaseView view: The view which raised the exception.
    :param Exception e: The exception.
    :return: A response
    """
    if isinstance(e, APIException):
        message = e
    elif isinstance(e, HTTPException):
        message = APIException(e.description)
        message.status_code = e.code
    else:
        debug = current_app.config.get('DEBUG')
        message = APIException(str(e)) if debug else APIException()

    return {'errors': message.denormalize()}, message.status_code


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
    def dispatch(self, *args, **kwargs):
        """
        Dispatches the incoming request to the particular method.
        :param args: The arguments parsed by Flask.
        :param kwargs: The arguments parsed by Flask.
        :return: A `flask.Response` instance.
        """


class View(BaseView):
    """
    The default view class that implements authentication, authorization,
    argument parsing, serialization, error handling.
    """

    def dispatch(self, *args, **kwargs):
        """
        Dispatches the incoming request to the particular method.
        :param args: The arguments parsed by Flask.
        :param kwargs: The arguments parsed by Flask.
        :return: A `flask.Response` instance.
        """
        try:
            return self._handle_request(*args, **kwargs)
        except Exception as e:
            return self._handle_exception(e)

    def _handle_request(self, *args, **kwargs):
        """
        Applies all steps of the pipeline on the incoming request.
        :return: A `flask.Response` instance.
        """
        response = request.action.func(self, *args, **kwargs)

        return self._make_response(response)

    def _handle_exception(self, e):
        """
        Handles any error that occurs, giving the opportunity for
        custom error handling by user code.
        :param Exception e: The exception.
        :return: A `flask.Response` instance.
        """
        response = request.action.exception_handler(self, e)

        return self._make_response(response, force_renderer=True)

    def _select_renderer(self, force=False):
        """
        Determines which renderer should be used to render the outgoing response.
        :param force: If set to `True` selects the first renderer when the appropriated is not found.
        :return: A tuple with renderer and the mimetype.
        """
        negotiator = request.action.content_negotiator
        renderers = request.action.renderers

        try:
            return negotiator.select_renderer(renderers)
        except NotAcceptable:
            if not force:
                raise
            return renderers[0], renderers[0].mimetype

    def _make_response(self, data, force_renderer=False):
        """
        Returns a `flask.Response` for the given data.
        The appropriated renderer is taken based on the request header Accept.
        If there is not data to be serialized the response status code is 204.

        :param data: The Python object to be serialized.
        :param bool force_renderer: If set to `True` selects the first renderer when the appropriated is not found.
        :return: A Flask response.
        """
        response_class = request.action.app.response_class

        status = headers = None
        if isinstance(data, tuple):
            data, status, headers = unpack(data)

        if not isinstance(data, response_class):
            if data is None:
                data = response_class(status=204)
            else:
                renderer, mimetype = self._select_renderer(force_renderer)
                data_bytes = renderer.render(data, mimetype)
                data = response_class(data_bytes, mimetype=str(mimetype))

        if status is not None:
            data.status_code = status

        if headers:
            data.headers.extend(headers)

        return data


class Action(object):
    """
    Represents a func in the View that should be
    treated as a Flask view.
    """

    def __init__(self, func, view, api):
        self.func = self.__apply_filters(func, view, api)
        self.view = view
        self.api = api
        self.app = api.app

        self.argument_providers = api.argument_providers
        self.content_negotiator = self.api.content_negotiator
        self.parsers = self.api.parsers
        self.renderers = self.api.renderers
        self.exception_handler = api.exception_handler

        if not reflect.has_self_argument(self.func):
            self.func = reflect.func_to_method(self.func)

    def __apply_filters(self, func, view, api):
        filters = getattr(func, 'filters', []) + \
                  getattr(view, 'filters', []) + \
                  getattr(api, 'filters', [])

        func = self.__apply_filters_by_type(exception_filter, func, filters)
        func = self.__apply_filters_by_type(action_filter, func, filters)
        func = self.__apply_filters_by_type(authorization_filter, func, filters)
        func = self.__apply_filters_by_type(authentication_filter, func, filters)

        return func

    def __apply_filters_by_type(self, filter_type, func, filters):
        filters = sorted(filter(lambda x: x[0] == filter_type, filters), key=lambda x: x[2])

        for _, f, _ in filters:
            func = f(func)

        return func

    def __get_attr(self, attribute_name):
        attribute_value = getattr(self.api, attribute_name, None)
        override_name = attribute_name + '_override'

        for obj in (self.view, self.func):
            value = getattr(obj, attribute_name, missing)
            if value is not missing:
                if getattr(obj, override_name, True):
                    attribute_value = value
                else:
                    attribute_value.extend(value)

        return attribute_value
