"""
Handles exceptions raised by Flask WebAPI.
"""

from . import status


class APIException(Exception):
    """
    Base class for Flask WebAPI exceptions.
    Subclasses should provide `.status_code` and `.default_message` properties.
    :param str message: The actual message.
    :param kwargs: The extra attributes.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message = 'A server error occurred.'

    def __init__(self, message=None, **kwargs):
        if message is not None:
            self.message = str(message)
        else:
            self.message = str(self.default_message)

        self.kwargs = kwargs

    def __str__(self):
        return self.message

    def denormalize(self, message_key_name='message', field_key_name='field'):
        """
        Turns all `APIException` instances into `dict` and
        returns a unique level of errors.
        :param message_key_name: The key name used for the message item.
        :param field_key_name: The key name used for the field item.
        :return: A list of errors.
        """
        errors = []

        self._denormalize(errors, self, message_key_name=message_key_name, field_key_name=field_key_name)

        return errors

    def _denormalize(self, errors, message, field=None, message_key_name='message', field_key_name='field'):
        kwargs = None

        if isinstance(message, APIException):
            kwargs = message.kwargs
            message = message.message

        if isinstance(message, dict):
            for f, messages in message.items():
                f = field + '.' + f if field else f
                self._denormalize(errors, messages, f, message_key_name, field_key_name)

        elif isinstance(message, list):
            for message in message:
                self._denormalize(errors, message, field, message_key_name, field_key_name)

        else:
            data = {message_key_name: message}

            if kwargs:
                data.update(kwargs)

            if field:
                data.update({field_key_name: field})

            errors.append(data)

        return errors


class BadRequest(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = 'Bad request.'


class ValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message, **kwargs):
        if isinstance(message, dict):
            result = {}

            for field, messages in message.items():
                if not isinstance(messages, ValidationError):
                    messages = ValidationError(messages)

                if isinstance(messages.message, str):
                    result[field] = [messages]
                else:
                    result[field] = messages.message

            self.message = result
            self.kwargs = {}

        elif isinstance(message, list):
            result = []
            for msg in message:
                if not isinstance(msg, ValidationError):
                    if isinstance(msg, dict):
                        msg = ValidationError(**msg)
                    else:
                        msg = ValidationError(msg)

                result.append(msg)

            self.message = result[0].message if len(result) == 1 else result
            self.kwargs = result[0].kwargs if len(result) == 1 else {}

        else:
            self.message = str(message)
            self.kwargs = kwargs

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return repr(self.message)

    def __repr__(self):
        return 'ValidationError(%s)' % self


class ParseError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = 'Malformed request.'


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
        if message is None:
            message = self.default_message.format(mimetype=mimetype)
        super().__init__(message)
