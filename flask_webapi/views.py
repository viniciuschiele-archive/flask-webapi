import inspect

from flask import request
from werkzeug.exceptions import HTTPException
from .actions import APIAction
from .authentication import perform_authentication
from .authorization import perform_authorization
from .errors import APIError, ErrorDetail, ServerError
from .negotiation import perform_content_negotiation
from .response import make_response
from .serialization import perform_serialization


def route(url, methods=None):
    def decorator(func):
        func.url = url
        func.methods = methods
        return func
    return decorator


class APIView(object):
    url = None
    authenticators = None
    permissions = None
    content_negotiator = None
    parsers = None
    renderers = None
    serializer = None

    def dispatch(self, *args, **kwargs):
        try:
            perform_authentication()
            perform_authorization()
            perform_content_negotiation()

            response = request.action(self, *args, **kwargs)

            response = perform_serialization(response)
            response = make_response(response)
        except Exception as e:
            response = self.handle_error(e)

        return response

    def handle_error(self, error):
        if isinstance(error, APIError):
            code = error.code
            err = error.errors
        elif isinstance(error, HTTPException):
            code = error.code
            err = [ErrorDetail(error.description)]
        else:
            code = ServerError.code
            err = [ErrorDetail(ServerError.default_message)]

        return make_response(([e.__dict__ for e in err], code))

    @classmethod
    def register(cls, api):
        app = api.app

        members = inspect.getmembers(cls, predicate=lambda obj: inspect.isfunction(obj) and hasattr(obj, 'url'))

        for _, func in members:
            action = APIAction(func, cls, api)
            app.add_url_rule(action.url, action.name, action.as_view(), methods=func.methods)
