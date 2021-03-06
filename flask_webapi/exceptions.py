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

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return str(self.message)

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


class ValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message, **kwargs):
        # if `message` is a dict the key is
        # the name of the field and the value is
        # actual message.
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

            if len(result) == 1:
                self.message = result[0].message
                self.kwargs = result[0].kwargs
            else:
                self.message = result
                self.kwargs = {}

        else:
            self.message = str(message)
            self.kwargs = kwargs


class UnsupportedMediaType(Exception):
    default_message = 'Unsupported media type "{mimetype}" in request.'

    def __init__(self, mimetype, message=None):
        if message is None:
            message = self.default_message.format(mimetype=mimetype)
        self.message = message
