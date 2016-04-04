"""
Provides a BaseView class that is the base of all views in Flask WebAPI.
"""

from flask import current_app
from werkzeug.exceptions import HTTPException
from .exceptions import APIException


def exception_handler(context):
    """
    Handles a specific error, by returning an appropriate response.
    :param ActionContext context: The context of the current action.
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
