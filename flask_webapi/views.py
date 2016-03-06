"""
Provides a ViewBase class that is the base of all views in Flask WebAPI.
"""

import inspect

from abc import ABCMeta
from flask import request
from werkzeug.exceptions import HTTPException
from .exceptions import APIException, NotAcceptable, NotAuthenticated, PermissionDenied, ValidationError
from .parsers import guess_location
from .serializers import Serializer
from .utils import get_attr, missing, unpack
from .utils.formatting import prepare_error_message_for_response


class ViewBase(metaclass=ABCMeta):
    """
    A base class from which all view classes should inherit.
    """
    context = None

    def dispatch(self, *args, **kwargs):
        try:
            self._authenticate()
            self._check_permissions()
            self._parse_arguments(kwargs)

            if self.context.has_self:
                response = self.context.func(self, *args, **kwargs)
            else:
                response = self.context.func(*args, **kwargs)

            return self._make_response(response, use_serializer=True)
        except Exception as e:
            return self._handle_error(e)

    def _authenticate(self):
        """
        Perform authentication on the incoming request.
        """
        request.user = None
        request.auth = None

        for auth in self.context.get_authenticators():
            auth_tuple = auth.authenticate()

            if auth_tuple:
                request.user = auth_tuple[0]
                request.auth = auth_tuple[1]
                break

    def _check_permissions(self):
        """
        Check if the request should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """

        for permission in self.context.get_permissions():
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
        negotiator = self.context.get_content_negotiator()
        renderers = self.context.get_renderers()

        renderer_pair = negotiator.select_renderer(renderers)

        if renderer_pair is None:
            if not force:
                raise NotAcceptable()

            renderer_pair = renderers[0], renderers[0].mimetype

        return renderer_pair
        # request.accepted_renderer, request.accepted_mimetype = renderer_pair

    def _parse_arguments(self, kwargs):
        if not self.context.params:
            return

        errors = {}

        params = self.context.get_params()

        for field_name, field in params.items():
            location = guess_location(field)
            func = self.context.api.parser_locations.get(location)

            if not func:
                raise Exception('location %s not found' % location)

            data = func(self.context)

            try:
                if isinstance(field, Serializer):
                    kwargs[field_name] = field.load(data, raise_exception=True)
                else:
                    value = field.get_value(data)
                    value = field.safe_deserialize(value)
                    kwargs[field_name] = None if value == missing else value
            except ValidationError as e:
                if e.has_fields:
                    errors.update(e.message)
                else:
                    errors[field.load_from] = e.message

        if errors:
            raise ValidationError(errors, has_fields=True)

    def _serialize_for_response(self, data):
        """
        Serializes the given data into a Python dict.

        :param data: The data to be serialized.
        :return: A Python dict object.
        """

        if not self.context.serializer:
            return data

        if data is None:
            return None

        serializer = self.context.get_serializer(**self.context.serializer_kwargs)

        return serializer.dump(data)

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
                data = self._serialize_for_response(data)

            if data is None:
                data = response_class(status=204)
            else:
                renderer, mimetype = self._select_renderer(force_renderer)
                data_bytes = renderer.render(data, mimetype)
                data = response_class(data_bytes, mimetype=mimetype.mimetype)

        if status is not None:
            data.status_code = status

        if headers:
            data.headers.extend(headers)

        return data

    def _handle_error(self, error):
        """
        Handles any error that occurs, giving the opportunity for
        custom error handling by user code.
        :param Exception error: The exception.
        :return: A response.
        """
        response = None

        if self.context.error_handler is not None:
            response = self.context.error_handler(error)

        if response is None:
            response = self._error_handler(error)

        return response

    def _error_handler(self, exc):
        """
        Handles a specific error, by returning an appropriate response.
        :param Exception exc: The exception.
        :return: A response
        """
        if isinstance(exc, ValidationError):
            code = exc.status_code
            message = exc.message
        elif isinstance(exc, APIException):
            code = exc.status_code
            message = [exc.message] if not isinstance(exc.message, list) else exc.message
        elif isinstance(exc, HTTPException):
            code = exc.code
            message = [exc.description]
        else:
            code = APIException.status_code
            message = [APIException.default_message]

        errors = []

        prepare_error_message_for_response(errors, message)

        return self._make_response((dict(errors=errors), code), force_renderer=True)


class ViewContext(object):
    def __init__(self, func, view, api):
        self.func = func
        self.view = view
        self.api = api
        self.app = api.app

        args = inspect.getargspec(func).args
        self.has_self = len(args) > 0 and args[0] == 'self'

        self.authenticators = get_attr((func, view), 'authenticators', api.authenticators)
        self.permissions = get_attr((func, view), 'permissions', api.permissions)
        self.content_negotiator = get_attr((func, view), 'content_negotiator', api.content_negotiator)
        self.parsers = get_attr((func, view), 'parsers', api.parsers)
        self.renderers = get_attr((func, view), 'renderers', api.renderers)
        self.params = getattr(func, 'params', None)
        self.serializer = get_attr((func, view), 'serializer', None)
        self.serializer_kwargs = getattr(func, 'serializer_kwargs', None)
        self.error_handler = get_attr((func, view), 'error_handler', api.error_handler)

    def get_authenticators(self):
        """
        Instantiates and returns the list of authenticators that this view can use.
        """
        return [authenticator() for authenticator in self.authenticators]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        return [permission() for permission in self.permissions]

    def get_content_negotiator(self):
        """
        Instantiates and returns the content negotiator that this action can use.
        """
        return self.content_negotiator()

    def get_parsers(self):
        """
        Instantiates and returns the list of parsers that this view can use.
        """
        return [parser() for parser in self.parsers]

    def get_renderers(self):
        """
        Instantiates and returns the list of renderers that this view can use.
        """
        return [renderer() for renderer in self.renderers]

    def get_params(self):
        """
        Instantiates and returns the serializer that this action can use.
        """
        return self.params

    def get_serializer(self, **kwargs):
        """
        Instantiates and returns the serializer that this action can use.
        """
        return self.serializer(**kwargs)
