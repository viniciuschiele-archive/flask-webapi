"""
Provides various validators.
"""

import re

from .exceptions import ValidationError


MISSING_ERROR_MESSAGE = (
    'ValidationError raised by `{class_name}`, but error key `{key}` does '
    'not exist in the `error_messages` dictionary.'
)


class ValidatorBase(object):
    """
    A base class from which all validator should inherit.

    :param dict error_messages: The error messages for various kinds of errors.
    """

    default_error_messages = {}

    def __init__(self, error_messages=None):
        messages = {}
        for cls in reversed(self.__class__.__mro__):
            messages.update(getattr(cls, 'default_error_messages', {}))
        messages.update(error_messages or {})
        self.error_messages = messages

    def _fail(self, key, **kwargs):
        """
        Raises a `ValidationError`.

        :param key: The key message to be fetched.
        :param kwargs: The kwargs used to replace the messages token.
        """
        try:
            message = self.error_messages[key]
            message = self._format_error(message, **kwargs)
            raise ValidationError(message)
        except KeyError:
            class_name = self.__class__.__name__
            msg = MISSING_ERROR_MESSAGE.format(class_name=class_name, key=key)
            raise AssertionError(msg)

    def _format_error(self, message, **kwargs):
        """
        Replaces the tokens by `kwargs`.

        :param message: The message that contains the tokens.
        :param kwargs: The args used to replace the tokens.
        :return: The message formatted.
        """
        if isinstance(message, str):
            message = message.format(**kwargs)
        elif message is dict:
            for key, value in message.items():
                message[key] = self._format_error(value, **kwargs)
        return message


class EmailValidator(ValidatorBase):
    """
    Validator which validates an email address.

    :param dict error_messages: The error messages for various kinds of errors.
    """

    USER_REGEX = re.compile(
        r"(^[-!#$%&'*+/=?^`{}|~\w]+(\.[-!#$%&'*+/=?^`{}|~\w]+)*$"  # dot-atom
        # quoted-string
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]'
        r'|\\[\001-\011\013\014\016-\177])*"$)', re.IGNORECASE | re.UNICODE)

    DOMAIN_REGEX = re.compile(
        # domain
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
        r'(?:[A-Z]{2,6}|[A-Z0-9-]{2,})$'
        # literal form, ipv4 address (SMTP 4.1.3)
        r'|^\[(25[0-5]|2[0-4]\d|[0-1]?\d?\d)'
        r'(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\]$', re.IGNORECASE | re.UNICODE)

    DOMAIN_WHITELIST = ('localhost',)

    default_error_messages = {
        'invalid': 'Not a valid email address.'
    }

    def __call__(self, value):
        if not value or '@' not in value:
            self._fail('invalid')

        user_part, domain_part = value.rsplit('@', 1)

        if not self.USER_REGEX.match(user_part):
            self._fail('invalid')

        if domain_part not in self.DOMAIN_WHITELIST:
            if not self.DOMAIN_REGEX.match(domain_part):
                try:
                    domain_part = domain_part.encode('idna').decode('ascii')
                except UnicodeError:
                    pass
                else:
                    if self.DOMAIN_REGEX.match(domain_part):
                        return
                self._fail('invalid')


class LengthValidator(ValidatorBase):
    """
    Validator which succeeds if the value passed to it has a length between a minimum and maximum.

    :param int min_length: The minimum length. If not provided, minimum length will not be checked.
    :param int max_length: The maximum length. If not provided, maximum length will not be checked.
    :param int equal_length: The exact length. If provided, maximum and minimum length will not be checked.
    :param dict error_messages: The error messages for various kinds of errors.
    """

    default_error_messages = {
        'min_length': 'Shorter than minimum length {min_length}.',
        'max_length': 'Longer than maximum length {max_length}.',
        'equal_length': 'Length must be {equal_length}.'
    }

    def __init__(self, min_length=None, max_length=None, equal_length=None, error_messages=None):
        if equal_length is not None and (min_length or max_length):
            raise ValueError('The `equal_length` parameter was provided, maximum or '
                             'minimum parameter must not be provided.')

        super().__init__(error_messages)

        self.min_length = min_length
        self.max_length = max_length
        self.equal_length = equal_length

    def __call__(self, value):
        length = len(value)

        if self.equal_length is not None:
            if length != self.equal_length:
                self._fail('equal_length', equal_length=self.equal_length)
            return

        if self.min_length is not None and length < self.min_length:
            self._fail('min_length', min_length=self.min_length)

        if self.max_length is not None and length > self.max_length:
            self._fail('max_length', max_length=self.max_length)


class RangeValidator(ValidatorBase):
    """
    Validator which succeeds if the value it is passed is greater
    or equal to ``min_value`` and less than or equal to ``max_value``.

    :param min_value: The minimum value (lower bound). If not provided, minimum value will not be checked.
    :param max_value: The maximum value (upper bound). If not provided, maximum value will not be checked.
    :param dict error_messages: The error messages for various kinds of errors.
    """

    default_error_messages = {
        'min_value': 'Must be at least {min_value}.',
        'max_value': 'Must be at most {max_value}.',
    }

    def __init__(self, min_value=None, max_value=None, error_messages=None):
        super().__init__(error_messages)

        self.min_value = min_value
        self.max_value = max_value

    def __call__(self, value):
        if self.min_value is not None and value < self.min_value:
            self._fail('min_value', min_value=self.min_value)

        if self.max_value is not None and value > self.max_value:
            self._fail('max_value', max_value=self.max_value)
