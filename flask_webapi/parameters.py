"""
Providers used to obtain the data for the parameters.
"""

from abc import ABCMeta, abstractmethod
from flask import request


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


class ArgumentProvider(metaclass=ABCMeta):
    """
    A base class from which all provider classes should inherit.
    """
    @abstractmethod
    def get_data(self, context):
        """
        Returns a `dict`.
        :param ViewContext context:
        :return dict:
        """


class QueryStringProvider(ArgumentProvider):
    """
    Provides arguments from the request's query string.
    """
    def get_data(self, context):
        return request.args


class FormDataProvider(ArgumentProvider):
    """
    Provides arguments from the request's form.
    """
    def get_data(self, context):
        return request.form


class HeaderProvider(ArgumentProvider):
    """
    Provides arguments from the request's headers.
    """
    def get_data(self, context):
        return request.headers


class CookieProvider(ArgumentProvider):
    """
    Provides arguments from the request's cookies.
    """
    def get_data(self, context):
        return request.cookies


class BodyProvider(ArgumentProvider):
    """
    Provides arguments from the request's body.
    """
    def get_data(self, context):
        negotiator = context.content_negotiator
        parsers = context.parsers

        parser, mimetype = negotiator.select_parser(parsers)

        stream = request._get_stream_for_parsing()

        return parser.parse(stream, mimetype)
