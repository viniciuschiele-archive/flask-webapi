import inspect

from flask import request
from werkzeug.exceptions import HTTPException
from .authentication import perform_authentication
from .authorization import perform_authorization
from .errors import APIError, ErrorDetail, ServerError
from .negotiation import DefaultContentNegotiator, perform_content_negotiation
from .renderers import JSONRenderer
from .serialization import perform_serialization
from .utils import get_attr, unpack
from .views import ViewAction


class WebAPI(object):
    def __init__(self, app=None):
        self.app = None
        self.authenticators = []
        self.permissions = []
        self.content_negotiator = DefaultContentNegotiator
        self.parsers = []
        self.renderers = [JSONRenderer]

        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app

    def add_view(self, view):
        self._register_view(view)

    def _register_view(self, view):
        members = inspect.getmembers(view, lambda obj: inspect.isfunction(obj) and hasattr(obj, '_url'))

        for name, func in members:
            action = ViewAction()
            action.func = func
            action.authenticators = get_attr((func, view), '_authenticators', self.authenticators)
            action.permissions = get_attr((func, view), '_permissions', self.permissions)
            action.content_negotiator = get_attr((func, view), '_content_negotiator', self.content_negotiator)
            action.parsers = get_attr((func, view), '_parsers', self.parsers)
            action.renderers = get_attr((func, view), '_renderers', self.renderers)
            action.serializer = get_attr((func, view), '_serializer', None)
            action.envelope = getattr(func, '_envelope', None)

            name = view.__name__ + ':' + func.__name__
            url = (getattr(view, '_url', None) or '') + (getattr(func, '_url', None) or '')

            self.app.add_url_rule(url, name, self._as_view(view, action), methods=func._methods)

    def _as_view(self, view, action):
        def view2(*args, **kwargs):
            return self._dispatch_request(view, action, *args, **kwargs)
        return view2

    def _dispatch_request(self, view, action, *args, **kwargs):
        request.action = action

        try:
            perform_authentication()
            perform_authorization()
            perform_content_negotiation()

            instance = view()
            response = action(instance, *args, **kwargs)

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
