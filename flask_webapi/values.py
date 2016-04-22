"""
Provides a set of classes to deal with input data.
"""

from abc import ABCMeta, abstractmethod
from flask import request
from .exceptions import ParseError, UnsupportedMediaType


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
