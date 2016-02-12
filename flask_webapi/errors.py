"""
Provides various exceptions raised by Flask WebAPI.
"""


class ErrorDetail(object):
    def __init__(self, message, **fields):
        if message is None:
            raise TypeError('\'NoneType\' object has no attribute \'message\'')

        self.message = message
        self.__dict__.update(fields)

    def __str__(self):
        return self.message


class APIError(Exception):
    code = None

    def __init__(self):
        self.errors = []

    def append(self, message, **fields):
        self.errors.append(ErrorDetail(message, **fields))
        return self

    def __str__(self):
        if self.errors:
            return str(self.errors[0])
        return ''


class SingleError(APIError):
    default_message = None

    def __init__(self, message=None, **fields):
        super().__init__()
        self.append(message or self.default_message, **fields)


class NotAcceptable(SingleError):
    code = 406
    default_message = 'Could not satisfy the request Accept header.'


class AuthenticationFailed(SingleError):
    code = 401
    default_message = 'Incorrect authentication credentials.'


class NotAuthenticated(SingleError):
    code = 401
    default_message = 'Authentication credentials were not provided.'


class PermissionDenied(SingleError):
    code = 403
    default_message = 'You do not have permission to perform this action.'


class ServerError(SingleError):
    code = 500
    default_message = 'A server error occurred.'
