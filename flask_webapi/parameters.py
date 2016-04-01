"""
Argument provider obtains the data for the parameters.
"""

from abc import ABCMeta, abstractmethod
from flask import request
from .exceptions import ValidationError
from .filters import action_filter
from .schemas import Schema


class param(action_filter):
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

    def before_action(self, context):
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

    def after_action(self, context):
        pass

    def _get_arguments(self, context):
        """
        Gets the argument data based on the location.
        :return: The data obtained.
        """
        if self.location is None:
            location = 'query' if request.method == 'GET' else 'body'
        else:
            location = self.location

        provider = context.argument_providers.get(location)

        if provider:
            return provider.get_data(context)

        raise Exception('Argument provider for location "%s" not found.' % location)


def get_argument_providers():
    """
    Gets all instances of argument providers.
    :return: A list of argument providers.
    """
    return {'query': QueryStringProvider(),
            'form': FormDataProvider(),
            'header': HeaderProvider(),
            'cookie': CookieProvider(),
            'body': BodyProvider()}


class BaseArgumentProvider(metaclass=ABCMeta):
    """
    A base class from which all provider classes should inherit.
    """
    @abstractmethod
    def get_data(self, context):
        """
        Returns the arguments as `dict`.
        :param ActionContext context:
        :return dict: The `dict` containing the arguments.
        """


class QueryStringProvider(BaseArgumentProvider):
    """
    Provides arguments from the request query string.
    """
    def get_data(self, context):
        return request.args


class FormDataProvider(BaseArgumentProvider):
    """
    Provides arguments from the request form.
    """
    def get_data(self, context):
        return request.form


class HeaderProvider(BaseArgumentProvider):
    """
    Provides arguments from the request headers.
    """
    def get_data(self, context):
        return dict(request.headers)


class CookieProvider(BaseArgumentProvider):
    """
    Provides arguments from the request cookies.
    """
    def get_data(self, context):
        return request.cookies


class BodyProvider(BaseArgumentProvider):
    """
    Provides arguments from the request body.
    """
    def get_data(self, context):
        negotiator = context.content_negotiator
        parsers = context.parsers

        parser, mimetype = negotiator.select_parser(parsers)

        # to avoid problems related to the input stream
        # we call get_data to cache the input data.
        request.get_data()

        stream = request._get_stream_for_parsing()

        return parser.parse(stream, mimetype)
