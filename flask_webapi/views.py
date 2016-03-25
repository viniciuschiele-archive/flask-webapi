"""
Provides a BaseView class that is the base of all views in Flask WebAPI.
"""


from abc import ABCMeta, abstractmethod
from flask import request, current_app
from werkzeug.exceptions import HTTPException
from .exceptions import APIException, NotAcceptable, NotAuthenticated, PermissionDenied, ValidationError
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
        self._authenticate()
        self._check_permission()
        self._parse_arguments(kwargs)

        response = request.action.func(self, *args, **kwargs)

        return self._make_response(response, use_serializer=True)

    def _handle_exception(self, e):
        """
        Handles any error that occurs, giving the opportunity for
        custom error handling by user code.
        :param Exception e: The exception.
        :return: A `flask.Response` instance.
        """
        response = request.action.exception_handler(self, e)

        return self._make_response(response, force_renderer=True)

    def _authenticate(self):
        """
        Perform authentication on the incoming request.
        """
        request.user = None
        request.auth = None

        for auth in request.action.authenticators:
            auth_tuple = auth.authenticate()

            if auth_tuple:
                request.user = auth_tuple[0]
                request.auth = auth_tuple[1]
                break

    def _check_permission(self):
        """
        Checks if the incoming request should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in request.action.permissions:
            if not permission.has_permission():
                if request.user:
                    raise PermissionDenied()
                else:
                    raise NotAuthenticated()

    def _get_arguments(self, location):
        """
        Gets the argument data based on the location.
        :param str location: The location to retrieve the data.
        :return: The data obtained.
        """
        if location is None:
            location = 'query' if request.method == 'GET' else 'body'

        provider = request.action.argument_providers.get(location)

        if provider:
            return provider.get_data()

        raise Exception('Argument provider for location "%s" not found.' % location)

    def _parse_arguments(self, kwargs):
        """
        Parses the incoming request and turn it into parameters.
        :param kwargs: The output parameters.
        """
        params = request.action.params

        if not params:
            return

        # to avoid problems related to the input stream
        # we call get_data to cache the input data.
        request.get_data()

        errors = {}

        for field_name, (field, location) in params.items():
            data = self._get_arguments(location)

            try:
                if isinstance(field, Schema):
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

    def _serialize_data(self, data):
        """
        Serializes the given data into a Python dict.
        :param data: The data to be serialized.
        :return: A Python dict object.
        """
        if data is None:
            return None

        serializer = request.action.serializer

        if not serializer:
            return data

        schema, many, envelope = serializer

        if many is None:
            many = isinstance(data, list)

        if many:
            data = schema.dumps(data)
        else:
            data = schema.dump(data)

        if envelope:
            data = {envelope: data}

        return data

    def _make_response(self, data, use_serializer=False, force_renderer=False):
        """
        Returns a `flask.Response` for the given data.
        The appropriated renderer is taken based on the request header Accept.
        If there is not data to be serialized the response status code is 204.

        :param data: The Python object to be serialized.
        :param bool use_serializer: If set to `True` the data has to be serialized.
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
                if use_serializer:
                    data = self._serialize_data(data)

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
        self.func = func
        self.view = view
        self.api = api
        self.app = api.app

        self.authenticators = self.__get_attr('authenticators')
        self.permissions = self.__get_attr('permissions')
        self.content_negotiator = self.__get_attr('content_negotiator')
        self.parsers = self.__get_attr('parsers')
        self.renderers = self.__get_attr('renderers')
        self.serializer = self.__get_attr('serializer')
        self.params = getattr(func, 'params', None)
        self.exception_handler = api.exception_handler
        self.argument_providers = api.argument_providers

        if not reflect.has_self_argument(func):
            self.func = reflect.func_to_method(func)

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
