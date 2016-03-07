"""
Handles exceptions raised by Flask WebAPI.
"""

from . import status


class APIException(Exception):
    """
    Base class for REST framework exceptions.
    Subclasses should provide `.status_code` and `.default_message` properties.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message = 'A server error occurred.'

    def __init__(self, message=None):
        if message is not None:
            self.message = message
        else:
            self.message = self.default_message

    def __str__(self):
        return str(self.message)


class ValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message, has_fields=False):
        if not isinstance(message, list) and not has_fields:
            message = [message]

        self.has_fields = has_fields
        self.message = message


class ParseError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Malformed request.'


class AuthenticationFailed(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_message = 'Incorrect authentication credentials.'


class NotAuthenticated(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_message = 'Authentication credentials were not provided.'


class PermissionDenied(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_message = 'You do not have permission to perform this action.'


class NotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = 'Not found.'


class NotAcceptable(APIException):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    default_message = 'Could not satisfy the request Accept header.'


class UnsupportedMediaType(APIException):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    default_message = 'Unsupported media type "{mimetype}" in request.'

    def __init__(self, mimetype, message=None):
        if message is not None:
            self.message = message
        else:
            self.message = self.default_message.format(mimetype=mimetype)
