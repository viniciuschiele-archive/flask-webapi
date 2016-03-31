"""
Argument provider obtains the data for the parameters.
"""

from abc import ABCMeta, abstractmethod
from flask import request
from .exceptions import ValidationError
from .filters import action_filter
from .schemas import Schema


@action_filter
def param(name, field, location=None):
    """
    A decorator that apply a argument parser to the action.
    :param str name: The name of the parameter.
    :param Field field: The field used to fill the parameter.
    :param str location: Where to retrieve the values.
    :return: A function.
    """

    if isinstance(field, type):
        field = field()

    is_schema = isinstance(field, Schema)

    if not is_schema:
        field = type('ParamSchema', (Schema,), {name: field})()

    def get_arguments():
        """
        Gets the argument data based on the location.
        :return: The data obtained.
        """
        if location is None:
            local_location = 'query' if request.method == 'GET' else 'body'
        else:
            local_location = location

        provider = request.action.argument_providers.get(local_location)

        if provider:
            return provider.get_data()

        raise Exception('Argument provider for location "%s" not found.' % local_location)

    def execute(func, *args, **kwargs):
        errors = {}

        data = get_arguments()

        try:
            result = field.load(data)

            if is_schema:
                kwargs[name] = result
            else:
                kwargs.update(result)
        except ValidationError as e:
            errors.update(e.message)

        if errors:
            raise ValidationError(errors)

        return func(*args, **kwargs)

    return execute


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
    def get_data(self):
        """
        Returns the arguments as `dict`.
        :return dict: The `dict` containing the arguments.
        """


class QueryStringProvider(BaseArgumentProvider):
    """
    Provides arguments from the request query string.
    """
    def get_data(self):
        return request.args


class FormDataProvider(BaseArgumentProvider):
    """
    Provides arguments from the request form.
    """
    def get_data(self):
        return request.form


class HeaderProvider(BaseArgumentProvider):
    """
    Provides arguments from the request headers.
    """
    def get_data(self):
        return dict(request.headers)


class CookieProvider(BaseArgumentProvider):
    """
    Provides arguments from the request cookies.
    """
    def get_data(self):
        return request.cookies


class BodyProvider(BaseArgumentProvider):
    """
    Provides arguments from the request body.
    """
    def get_data(self):
        action = request.action

        negotiator = action.content_negotiator
        parsers = action.parsers

        parser, mimetype = negotiator.select_parser(parsers)

        # to avoid problems related to the input stream
        # we call get_data to cache the input data.
        request.get_data()

        stream = request._get_stream_for_parsing()

        return parser.parse(stream, mimetype)
