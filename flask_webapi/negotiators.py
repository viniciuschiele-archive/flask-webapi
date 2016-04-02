"""
Content negotiation selects a appropriated parser and renderer for a HTTP request.
"""

from abc import ABCMeta, abstractmethod
from flask import request
from .exceptions import NotAcceptable, UnsupportedMediaType
from .formatters import MimeType


class BaseContentNegotiator(metaclass=ABCMeta):
    """
    Base class for all content negotiations.
    """

    @abstractmethod
    def select_input_formatter(self, formatters):
        """
        Selects the appropriated parser for the given request.
        :param formatters: The lists of input formatters.
        :return: The parser selected or raise `UnsupportedMediaType`.
        """

    @abstractmethod
    def select_output_formatter(self, formatters):
        """
        Selects the appropriated renderer for the given request.
        :param formatters: The lists of output formatters.
        :return: The renderer selected or raise `NotAcceptable`.
        """


class DefaultContentNegotiator(BaseContentNegotiator):
    """
    Selects a parser by request content type and a
    renderer by request accept.
    """

    def select_input_formatter(self, formatters):
        """
        Selects the appropriated parser that matches to the request's content type.
        :param formatters: The lists of input formatters.
        :return: The parser selected or raise `UnsupportedMediaType`.
        """
        mimetype = MimeType.parse(request.content_type)

        for formatter in formatters:
            if mimetype.match(formatter.mimetype):
                return formatter, mimetype

        raise UnsupportedMediaType(request.content_type)

    def select_output_formatter(self, formatters):
        """
        Selects the appropriated parser that matches to the request's accept header.
        :param formatters: The lists of output formatters.
        :return: The parser selected or raise `NotAcceptable`.
        """
        for mimetype in self._get_accept_list():
            accept_mimetype = MimeType.parse(mimetype)
            for formatter in formatters:
                if accept_mimetype.match(formatter.mimetype):
                    return formatter, formatter.mimetype.replace(params=accept_mimetype.params)

        raise NotAcceptable()

    def _get_accept_list(self):
        """
        Given the incoming request, return a list of accepted media type strings.
        """
        header = request.environ.get('HTTP_ACCEPT') or '*/*'
        return [token.strip() for token in header.split(',')]
