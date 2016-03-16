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
from .utils.formatting import prepare_error_message_for_response


def exception_handler(view, e):
    """
    Handles a specific error, by returning an appropriate response.
    :param ViewBase view: The view which raised the exception.
    :param Exception e: The exception.
    :return: A response
    """
    if isinstance(e, ValidationError):
        code = e.status_code
        message = e.message
    elif isinstance(e, APIException):
        code = e.status_code
        message = [e.message] if not isinstance(e.message, list) else e.message
    elif isinstance(e, HTTPException):
        code = e.code
        message = [e.description]
    else:
        debug = current_app.config.get('DEBUG')
        code = APIException.status_code
        message = [str(e)] if debug else [APIException.default_message]

    errors = []

    prepare_error_message_for_response(errors, message)

    return {'errors': errors}, code


class ViewBase(metaclass=ABCMeta):
    """
    A base class from which all view classes should inherit.
    """
    _context = None

    @property
    def context(self):
        if not self._context:
            raise Exception()
        return self._context

    def dispatch(self, context, *args, **kwargs):
        try:
            self._context = context

            self._authenticate()
            self._check_permission()
            self._parse_arguments(kwargs)

            if self.context.has_self:
                response = self.context.func(self, *args, **kwargs)
            else:
                response = self.context.func(*args, **kwargs)

            return self._make_response(response, use_serializer=True)
        except Exception as e:
            return self._handle_exception(e)

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

    def _select_renderer(self, force=False):
        """
        Determine which parser and renderer to be used to parse the incoming request
        and to render the outgoing response.

        :param force: True to select the first parser/renderer when the appropriated is not found.
        """
        negotiator = self.context.content_negotiator
        renderers = self.context.renderers

        renderer_pair = negotiator.select_renderer(renderers)

        if renderer_pair is None:
            if not force:
                raise NotAcceptable()

            renderer_pair = renderers[0], renderers[0].mimetype

        return renderer_pair

    def _parse_data(self, location):
        """
        Parses the data from the incoming request for a specified field.
        :param str location: The location to retrieve the data.
        :return: The data parsed from the incoming request.
        """
        if location is None:
            if request.method == 'GET':
                location = 'query'
            elif request.content_type == 'application/x-www-form-urlencoded':
                location = 'form'
            else:
                location = 'body'

        func = self.context.api.parser_locations.get(location)

        if not func:
            raise Exception('Parse location %s not found.' % location)

        return func(self.context)

    def _parse_arguments(self, kwargs):
        """
        Parses the incoming request and turn it into parameters.
        :param kwargs: The output parameters.
        """
        params = self.context.params

        if not params:
            return

        errors = {}

        for field_name, (field, location) in params.items():
            data = self._parse_data(location)

            try:
                if isinstance(field, Serializer):
                    kwargs[field_name] = field.load(data)
                else:
                    value = field.get_value(data)
                    value = field.load(value)
                    if value is not missing:
                        kwargs[field_name] = value
            except ValidationError as e:
                if e.has_fields:
                    errors.update(e.message)
                else:
                    errors[field.load_from] = e.message

        if errors:
            raise ValidationError(errors, has_fields=True)

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

    def _handle_exception(self, e):
        """
        Handles any error that occurs, giving the opportunity for
        custom error handling by user code.
        :param Exception e: The exception.
        :return: A response.
        """
        response = self.context.exception_handler(self, e)

        return self._make_response(response, force_renderer=True)


class ViewContext(object):
    def __init__(self, func, view, api):
        self.func = func
        self.view = view
        self.api = api
        self.app = api.app

        args = inspect.getargspec(func).args
        self.has_self = len(args) > 0 and args[0] == 'self'

        self.authenticators = self.__get_value('authenticators')
        self.permissions = self.__get_value('permissions')
        self.content_negotiator = self.__get_value('content_negotiator')
        self.parsers = self.__get_value('parsers')
        self.renderers = self.__get_value('renderers')
        self.params = getattr(func, 'params', None)
        self.serializer = getattr(func, 'serializer', None)
        self.serializer_args = getattr(func, 'serializer_args', None)
        self.exception_handler = api.exception_handler

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
