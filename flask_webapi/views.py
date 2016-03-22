"""
Provides a ViewBase class that is the base of all views in Flask WebAPI.
"""

import inspect

from abc import ABCMeta
from flask import request, current_app
from werkzeug.exceptions import HTTPException
from .exceptions import APIException, NotAcceptable, NotAuthenticated, PermissionDenied, ValidationError
from .serializers import Serializer
from .utils import missing, unpack


def exception_handler(view, e):
    """
    Handles a specific error, by returning an appropriate response.
    :param ViewBase view: The view which raised the exception.
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


class BaseView(metaclass=ABCMeta):
    """
    A base class from which all view classes should inherit.
    """
    context = None

    def dispatch(self, context, *args, **kwargs):
        try:
            self.context = context
            return self._handle_request(*args, **kwargs)
        except Exception as e:
            return self._handle_exception(e)

    def _handle_request(self, *args, **kwargs):
        self._authenticate()
        self._check_permission()
        self._parse_arguments(kwargs)

        response = self.context.func(self, *args, **kwargs)

        return self._make_response(response, use_serializer=True)

    def _handle_exception(self, e):
        """
        Handles any error that occurs, giving the opportunity for
        custom error handling by user code.
        :param Exception e: The exception.
        :return: A response.
        """
        response = self.context.exception_handler(self, e)

        return self._make_response(response, force_renderer=True)

    def _authenticate(self):
        """
        Perform authentication on the incoming request.
        """
        request.user = None
        request.auth = None

        for auth in self.context.authenticators:
            auth_tuple = auth.authenticate()

            if auth_tuple:
                request.user = auth_tuple[0]
                request.auth = auth_tuple[1]
                break

    def _check_permission(self):
        """
        Check if the request should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """

        for permission in self.context.permissions:
            if not permission.has_permission():
                if request.user:
                    raise PermissionDenied()
                else:
                    raise NotAuthenticated()

    def _get_arguments(self, location):
        """
        Parses the data from the incoming request for a specified field.
        :param str location: The location to retrieve the data.
        :return: The data parsed from the incoming request.
        """

        if location is None:
            location = 'query' if request.method == 'GET' else 'body'

        provider = self.context.argument_providers.get(location)

        if provider:
            return provider.get_data(self.context)

        raise Exception('Argument provider for location "%s" not found.' % location)

    def _parse_arguments(self, kwargs):
        """
        Parses the incoming request and turn it into parameters.
        :param kwargs: The output parameters.
        """
        params = self.context.params

        if not params:
            return

        # to avoid problems related to the input stream
        # we call get_data to cache the input data.
        request.get_data()

        errors = {}

        for field_name, (field, location) in params.items():
            data = self._get_arguments(location)

            try:
                if isinstance(field, Serializer):
                    kwargs[field_name] = field.load(data)
                else:
                    value = field.get_value(data)
                    value = field.load(value)
                    if value is not missing:
                        kwargs[field_name] = value
            except ValidationError as e:
                if isinstance(e.message, dict):
                    errors.update(e.message)
                else:
                    errors[field.load_from] = e.message

        if errors:
            raise ValidationError(errors)

    def _select_renderer(self, force=False):
        """
        Determine which parser and renderer to be used to parse the incoming request
        and to render the outgoing response.

        :param force: True to select the first parser/renderer when the appropriated is not found.
        """
        negotiator = self.context.content_negotiator
        renderers = self.context.renderers

        try:
            return negotiator.select_renderer(renderers)
        except NotAcceptable:
            if force:
                return renderers[0], renderers[0].mimetype
            raise

    def _serialize_data(self, data):
        """
        Serializes the given data into a Python dict.

        :param data: The data to be serialized.
        :return: A Python dict object.
        """

        if not self.context.serializer:
            return data

        if data is None:
            return None

        serializer = self.context.serializer

        if self.context.serializer_args.get('many'):
            data = serializer.dumps(data)
        else:
            data = serializer.dump(data)

        envelope = self.context.serializer_args.get('envelope')

        if envelope:
            data = {envelope: data}

        return data

    def _make_response(self, data, use_serializer=False, force_renderer=False):
        """
        Returns a response object from the specified data.
        The appropriated renderer is taken based on the request header Accept.
        If there is not data to be serialized the response status code is 204.

        :param data: The Python object to be serialized.
        :param use_serializer: True if the data has to be serialized.
        :return: A Flask response.
        """
        response_class = self.context.app.response_class

        status = headers = None
        if isinstance(data, tuple):
            data, status, headers = unpack(data)

        if not isinstance(data, response_class):
            if use_serializer:
                data = self._serialize_data(data)

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


class ViewContext(object):
    def __init__(self, func, view, api):
        self.func = func
        self.view = view
        self.api = api
        self.app = api.app

        self.authenticators = self.__get_value('authenticators')
        self.permissions = self.__get_value('permissions')
        self.content_negotiator = self.__get_value('content_negotiator')
        self.parsers = self.__get_value('parsers')
        self.renderers = self.__get_value('renderers')
        self.params = getattr(func, 'params', None)
        self.serializer = getattr(func, 'serializer', None)
        self.serializer_args = getattr(func, 'serializer_args', None)
        self.exception_handler = api.exception_handler
        self.argument_providers = api.argument_providers

        func_args = inspect.getargspec(func).args
        if len(func_args) == 0 or func_args[0] != 'self':
            f = self.func
            self.func = lambda _, *args, **kwargs: f(*args, **kwargs)

    def __get_value(self, attribute_name):
        value = getattr(self.api, attribute_name, None)
        override_name = attribute_name + '_override'

        for obj in (self.view, self.func):
            obj_value = getattr(obj, attribute_name, missing)
            if obj_value is not missing:
                override = getattr(obj, override_name, True)
                if override:
                    value = obj_value
                else:
                    value.extend(obj_value)

        return value
