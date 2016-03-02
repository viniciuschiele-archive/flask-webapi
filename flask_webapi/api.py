"""
Provides the main class for Flask WebAPI.
"""

import inspect

from flask import request
from werkzeug.exceptions import HTTPException
from werkzeug.utils import import_string
from . import locations
from .controllers import ControllerAction, ControllerBase
from .exceptions import APIException, NotAcceptable, NotAuthenticated, PermissionDenied, ValidationError
from .negotiation import DefaultContentNegotiator
from .renderers import JSONRenderer
from .serializers import Serializer
from .utils import error, missing, unpack


class WebAPI(object):
    """
    The main entry point for the application.
    You need to initialize it with a Flask Application: ::

    >>> app = Flask(__name__)
    >>> api = WebAPI(app)

    Alternatively, you can use :meth:`init_app` to set the Flask application
    after it has been constructed.
    """

    def __init__(self, app=None):
        """
        Initialize this class with the given :class:`flask.Flask` application
        :param app: the Flask application
        :type app: flask.Flask
        Examples::
            api = WebAPI()
            api.add_controller(...)
            api.init_app(app)
        """
        self._controllers = []

        self.app = None
        self.authenticators = []
        self.permissions = []
        self.content_negotiator = DefaultContentNegotiator
        self.parsers = []
        self.renderers = [JSONRenderer]
        self.error_handler = None

        self.locations = {'query': locations.load_query}

        if app:
            self.init_app(app)

    def add_controller(self, controller):
        """
        Adds a controller to the WebAPI.
        :param ControllerBase controller: the class of your controller
        """
        if self.app:
            self._register_controller(controller)
        else:
            self._controllers.append(controller)

    def import_controllers(self, module):
        """
        Tries to import modules and register its controllers.
        :param module: The path of the module or the module itself.
        """
        if type(module) is str:
            module = import_string(module)

        members = inspect.getmembers(module)

        for _, member in members:
            if inspect.isfunction(member) and hasattr(member, 'url'):
                self.add_controller(member)
            elif inspect.isclass(member) and issubclass(member, ControllerBase) and member != ControllerBase:
                self.add_controller(member)

    def init_app(self, app):
        """
        Initialize this class with the given :class:`flask.Flask` application
        :param app: the Flask application
        :type app: flask.Flask
        Examples::
            api = WebAPI()
            api.add_controller(...)
            api.init_app(app)
        """
        self.app = app

        # gets all the module paths from the config
        # and import them to register its controllers.
        modules = self.app.config.get('WEBAPI_IMPORTS')
        if modules:
            for module in modules:
                self.import_controllers(module)

        # register all controllers added before the initialization
        if self._controllers:
            for controller in self._controllers:
                self._register_controller(controller)

    def _dispatch_request(self, *args, **kwargs):
        """
        Dispatches the current request through the WebAPI pipeline.
        """
        try:
            self._perform_authentication()
            self._perform_authorization()
            self._perform_content_negotiation()
            self._perform_deserialization(kwargs)

            action = request.action

            instance = action.controller()

            if action.has_self_param:
                response = action.func(instance, *args, **kwargs)
            else:
                response = action.func(*args, **kwargs)

            return self._make_response(response, use_serializer=True)
        except Exception as e:
            return self._handle_error(e)

    def _handle_error(self, error):
        """
        Handles any error that occurs, giving the opportunity for
        custom error handling by user code.
        :param Exception error: The exception.
        :return: A response.
        """
        action = request.action

        response = None

        if action.error_handler is not None:
            response = action.error_handler(error)

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

        error.prepare_error_message_for_response(errors, message)

        return self._make_response((dict(errors=errors), code))

    def _make_endpoint(self, controller, func):
        """
        Returns a endpoint for the specified controller and func.
        :param ControllerBase controller: the class of your controller
        :param func: the function of your controller
        :return: the endpoint
        """
        return controller.__name__ + ':' + func.__name__

    def _make_response(self, data, use_serializer=False):
        """
        Returns a response object from the specified data.
        The appropriated renderer is taken based on the request header Accept.
        If there is not data to be serialized the response status code is 204.

        :param data: The Python object to be serialized.
        :param use_serializer: True if the data has to be serialized.
        :return: A Flask response.
        """
        response_class = self.app.response_class

        status = headers = None
        if isinstance(data, tuple):
            data, status, headers = unpack(data)

        if not isinstance(data, response_class):
            if use_serializer:
                data = self._perform_serialization(data)

            if data is None:
                data = response_class(status=204)
            else:
                if not hasattr(request, 'accepted_renderer'):
                    self._perform_content_negotiation(force=True)

                data_bytes = request.accepted_renderer.render(data, request.accepted_mimetype)
                data = response_class(data_bytes, mimetype=request.accepted_mimetype.mimetype)

        if status is not None:
            data.status_code = status

        if headers:
            data.headers.extend(headers)

        return data

    def _make_view(self, action):
        """
        Returns a view method expected by Flask.
        :param ControllerAction action: the action
        :return: A function
        """
        def view(*args, **kwargs):
            request.action = action
            return self._dispatch_request(*args, **kwargs)
        return view

    def _perform_authentication(self):
        """
        Perform authentication on the incoming request.
        """
        request.user = None
        request.auth = None

        for auth in request.action.get_authenticators():
            auth_tuple = auth.authenticate()

            if auth_tuple:
                request.user = auth_tuple[0]
                request.auth = auth_tuple[1]
                break

    def _perform_authorization(self):
        """
        Check if the request should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """

        for permission in request.action.get_permissions():
            if not permission.has_permission():
                if request.user:
                    raise PermissionDenied()
                else:
                    raise NotAuthenticated()

    def _perform_content_negotiation(self, force=False):
        """
        Determine which parser and renderer to be used to parse the incoming request
        and to render the outgoing response.

        :param force: True to select the first parser/renderer when the appropriated is not found.
        """
        action = request.action

        negotiator = action.get_content_negotiator()
        renderers = action.get_renderers()

        renderer_pair = negotiator.select_renderer(renderers)

        if renderer_pair is None:
            if not force:
                raise NotAcceptable()

            renderer_pair = renderers[0], renderers[0].mimetype

        request.accepted_renderer, request.accepted_mimetype = renderer_pair

    def _perform_deserialization(self, kwargs):
        if not request.action.params:
            return

        params = request.action.get_params()

        for field_name, field in params.items():
            location = locations.guess_location(field)
            func = self.locations.get(location)
            if not func:
                raise Exception()

            data = func()

            if isinstance(field, Serializer):
                kwargs[field_name] = field.load(data, raise_exception=True)
            else:
                try:
                    value = field.get_value(data)
                    value = field.safe_deserialize(value)
                    kwargs[field_name] = None if value == missing else value
                except ValidationError as e:
                    raise ValidationError({field.load_from: e.message}, has_fields=True)

    def _perform_serialization(self, data):
        """
        Serializes the given data into a Python dict.

        :param data: The data to be serialized.
        :return: A Python dict object.
        """

        if not request.action.serializer:
            return data

        if data is None:
            return None

        serializer = request.action.get_serializer(**request.action.serializer_kwargs)

        return serializer.dump(data)

    def _register_controller(self, controller):
        """
        Registers a controller into Flask.
        :param ControllerBase controller: the controller to be registered.
        """
        if inspect.isfunction(controller):
            controller = type('WrappedControllerBase', (ControllerBase,), {controller.__name__: controller})

        members = inspect.getmembers(controller, lambda obj: inspect.isfunction(obj) and hasattr(obj, 'url'))

        for name, func in members:
            action = ControllerAction(func, controller, self)
            endpoint = self._make_endpoint(controller, func)

            self.app.add_url_rule(action.url, endpoint, self._make_view(action), methods=action.allowed_methods)
