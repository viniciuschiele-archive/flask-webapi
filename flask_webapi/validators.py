from .exceptions import ValidationError


class MaxLengthValidator(object):
    message = 'Longer than maximum length {max_length}.'

    def __init__(self, max_length, message=None):
        self.max_length = max_length

        if message:
            self.message = message

    def __call__(self, value):
        if len(value) > self.max_length:
            raise ValidationError(self._format_error(value, self.message))

        return value

    def _format_error(self, value, message):
        return (self.message or message).format(input=value, max_length=self.max_length)


class MinLengthValidator(object):
    message = 'Shorter than minimum length {min_length}.'

    def __init__(self, min_length, message=None):
        self.min_length = min_length

        if message:
            self.message = message

    def __call__(self, value):
        if len(value) < self.min_length:
            raise ValidationError(self._format_error(value, self.message))

        return value

    def _format_error(self, value, message):
        return (self.message or message).format(input=value, min_length=self.min_length)


class MaxValueValidator(object):
    message = 'Must be at most {max_value}.'

    def __init__(self, max_value, message=None):
        self.max_value = max_value

        if message:
            self.message = message

    def __call__(self, value):
        if value > self.max_value:
            raise ValidationError(self._format_error(value, self.message))

        return value

    def _format_error(self, value, message):
        return (self.message or message).format(input=value, max_value=self.max_value)


class MinValueValidator(object):
    message = 'Must be at least {min_value}.'

    def __init__(self, min_value, message=None):
        self.min_value = min_value

        if message:
            self.message = message

    def __call__(self, value):
        if value < self.min_value:
            raise ValidationError(self._format_error(value, self.message))

        return value

    def _format_error(self, value, message):
        return (self.message or message).format(input=value, min_value=self.min_value)
