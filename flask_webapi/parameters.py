"""
Argument provider obtains the data for the parameters.
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
        return request.headers


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

        stream = request._get_stream_for_parsing()

        return parser.parse(stream, mimetype)
