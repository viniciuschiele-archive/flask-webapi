"""
Provides a set of classes to deal with input data.
"""

from abc import ABCMeta, abstractmethod
from flask import request
from .exceptions import UnsupportedMediaType
from .utils.mimetypes import MimeType


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
        formatters = context.input_formatters

        formatter_pair = self._select_input_formatter(formatters)

        if formatter_pair is None:
            raise UnsupportedMediaType(request.content_type)

        formatter, mimetype = formatter_pair

        return formatter.read(request, mimetype)

    def _select_input_formatter(self, formatters):
        """
        Selects the appropriated formatter that matches with the request content type.
        :param formatters: The lists of input formatters.
        :return: The formatter selected or `None`.
        """
        mimetype = MimeType.parse(request.content_type)

        for formatter in formatters:
            if mimetype.match(formatter.mimetype):
                return formatter, mimetype

        return None
