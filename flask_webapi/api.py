import inspect

from flask import request
from werkzeug.exceptions import HTTPException
from .authentication import perform_authentication
from .authorization import perform_authorization
from .errors import APIError, ErrorDetail, ServerError
from .negotiation import DefaultContentNegotiator, perform_content_negotiation
from .renderers import JSONRenderer
from .serialization import perform_serialization
from .utils import unpack
from .views import ViewAction, ViewBase


class WebAPI(object):
    def __init__(self, app=None):
        """
        Initialize this class with the given :class:`flask.Flask` application
        :param app: the Flask application
        :type app: flask.Flask
        Examples::
            api = WebAPI()
            api.add_view(...)
            api.init_app(app)
        """
        self._views = []

        self.app = None
        self.authenticators = []
        self.permissions = []
        self.content_negotiator = DefaultContentNegotiator
        self.parsers = []
        self.renderers = [JSONRenderer]

        if app:
            self.init_app(app)

    def add_view(self, view):
        """
        Adds a view to the web api.
        :param view: the class of your view
        :type view: :class:`ViewBase`
        """
        if self.app:
            self._register_view(view)
        else:
            self._views.append(view)

    def init_app(self, app):
        """
        Initialize this class with the given :class:`flask.Flask` application
        :param app: the Flask application
        :type app: flask.Flask
        Examples::
            api = WebAPI()
            api.add_view(...)
            api.init_app(app)
        """
        self.app = app

        if self._views:
            for view in self._views:
                self._register_view(view)

    def _as_view(self, action):
        def view(*args, **kwargs):
            request.action = action
            return self._dispatch_request(*args, **kwargs)
        return view

    def _dispatch_request(self, *args, **kwargs):
        try:
            perform_authentication()
            perform_authorization()
            perform_content_negotiation()

            action = request.action

            instance = action.view()

            if action.has_self_param:
                response = action.func(instance, *args, **kwargs)
            else:
                response = action.func(*args, **kwargs)

            return self._make_response(response, use_serializer=True)
        except Exception as e:
            return self._handle_error(e)

    def _handle_error(self, error):
        if isinstance(error, APIError):
            code = error.code
            err = error.errors
        elif isinstance(error, HTTPException):
            code = error.code
            err = [ErrorDetail(error.description)]
        else:
            code = ServerError.code
            err = [ErrorDetail(ServerError.default_message)]

        return self._make_response(([e.__dict__ for e in err], code))

    def _make_endpoint(self, view, func):
        return view.__name__ + ':' + func.__name__

    def _make_response(self, data, use_serializer=False):
        """
        Creates a Flask response object from the specified data.
        The appropriated encoder is taken based on the request header Accept.
        If there is not data to be serialized the response status code is 204.

        :param data: The Python object to be serialized.
        :param use_serializer:
        :return: A Flask response object.
        """

        response_class = self.app.response_class

        status = headers = None
        if isinstance(data, tuple):
            data, status, headers = unpack(data)

        if not isinstance(data, response_class):
            if use_serializer:
                data = perform_serialization(data)

            if data is None:
                data = response_class(status=204)
            else:
                if not hasattr(request, 'accepted_renderer'):
                    perform_content_negotiation(force=True)

                data_bytes = request.accepted_renderer.render(data, request.accepted_mimetype)
                data = response_class(data_bytes, mimetype=request.accepted_mimetype.mimetype)

        if status is not None:
            data.status_code = status

        if headers:
            data.headers.extend(headers)

        return data

    def _register_view(self, view):
        if inspect.isfunction(view):
            view = type('WrappedViewBase', (ViewBase,), {view.__name__: view})

        members = inspect.getmembers(view, lambda obj: inspect.isfunction(obj) and hasattr(obj, '_url'))

        for name, func in members:
            action = ViewAction(func, view, self)
            endpoint = self._make_endpoint(view, func)

            self.app.add_url_rule(action.url, endpoint, self._as_view(action), methods=action.allowed_methods)
