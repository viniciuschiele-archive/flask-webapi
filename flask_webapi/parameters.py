"""
Provides a set of classes to deal with input data.
"""

from abc import ABCMeta, abstractmethod
from flask import request
from .exceptions import ParseError, UnsupportedMediaType, ValidationError
from .filters import ActionFilter, filter
from .serialization import Schema


def get_default_providers():
    """
    Gets all instances of value providers.
    :return: A list of value providers.
    """
    return {'query': QueryStringProvider(),
            'form': FormDataProvider(),
            'headers': HeadersProvider(),
            'cookies': CookiesProvider(),
            'body': BodyProvider()}


@filter()
class Parameter(ActionFilter):
    """
    Filter that retrieve a specific parameter from a specific location.
    :param str name: The name of parameter.
    :param Field field: The field used to parse the argument.
    :param str location: The location from where to retrieve the value.
    """
    def __init__(self, name, field, location=None, order=-1):
        super().__init__(order)

        if isinstance(field, type):
            field = field()

        self.is_schema = isinstance(field, Schema)

        if not self.is_schema:
            field = type('ParamSchema', (Schema,), {name: field})()

        self.name = name
        self.field = field
        self.location = location

    def pre_action(self, context):
        errors = {}

        data = self._get_arguments(context)

        try:
            result = self.field.load(data)

            if self.is_schema:
                context.kwargs[self.name] = result
            else:
                context.kwargs.update(result)
        except ValidationError as e:
            errors.update(e.message)

        if errors:
            raise ValidationError(errors)

    def post_action(self, context):
        pass

    def _get_arguments(self, context):
        """
        Gets the argument data based on the location.
        :return: The data obtained.
        """
        if not self.location:
            location = 'query' if request.method == 'GET' else 'body'
        else:
            location = self.location

        provider = context.value_providers.get(location)

        if provider is None:
            raise Exception('Value provider for location "%s" not found.' % location)

        return provider.get_data(context)


class ValueProvider(metaclass=ABCMeta):
    """
    A base class from which all provider classes should inherit.
    """
    @abstractmethod
    def get_data(self, context):
        """
        Returns the arguments as `dict`.
        :param ActionContext context: The action context.
        :return dict: The `dict` containing the arguments.
        """


class QueryStringProvider(ValueProvider):
    """
    Provides arguments from the request query string.
    """
    def get_data(self, context):
        return request.args


class FormDataProvider(ValueProvider):
    """
    Provides arguments from the request form.
    """
    def get_data(self, context):
        return request.form


class HeadersProvider(ValueProvider):
    """
    Provides arguments from the request headers.
    """
    def get_data(self, context):
        return dict(request.headers)


class CookiesProvider(ValueProvider):
    """
    Provides arguments from the request cookies.
    """
    def get_data(self, context):
        return request.cookies


class BodyProvider(ValueProvider):
    """
    Provides arguments from the request body.
    """
    def get_data(self, context):
        negotiator = context.content_negotiator
        formatters = context.input_formatters

        formatter_pair = negotiator.select_input_formatter(formatters)

        if formatter_pair is None:
            raise UnsupportedMediaType(request.content_type)

        formatter, mimetype = formatter_pair

        try:
            return formatter.read(request, mimetype)
        except ValueError as e:
            raise ParseError('Parse error: ' + str(e))


param = Parameter
