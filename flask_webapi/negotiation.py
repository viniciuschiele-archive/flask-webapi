"""
Content negotiation selects a appropriated parser and renderer for a HTTP request.
"""

from abc import ABCMeta, abstractmethod
from flask import request
from .exceptions import NotAcceptable, UnsupportedMediaType
from .utils.mimetypes import MimeType


class ContentNegotiatorBase(metaclass=ABCMeta):
    """
    Base class for all content negotiations.
    """

    @abstractmethod
    def select_parser(self, parsers):
        """
        Selects the appropriated parser for the given request.
        :param parsers: The lists of parsers.
        :return: The parser selected or raise an exception.
        """

    @abstractmethod
    def select_renderer(self, renderers):
        """
        Selects the appropriated renderer for the given request.
        :param renderers: The lists of renderers.
        :return: The renderer selected or raise an exception.
        """


class DefaultContentNegotiator(ContentNegotiatorBase):
    """
    Selects a parser by request content type and a
    renderer by request accept.
    """

    def select_parser(self, parsers):
        """
        Selects the appropriated parser which matches to the request's content type.
        :param parsers: The lists of parsers.
        :return: The parser selected or raise an exception.
        """
        mimetype = MimeType.parse(request.content_type)

        for parser in parsers:
            if mimetype.match(parser.mimetype):
                return parser, mimetype

        raise UnsupportedMediaType(request.content_type)

    def select_renderer(self, renderers):
        """
        Selects the appropriated parser which matches to the request's accept.
        :param renderers: The lists of parsers.
        :return: The parser selected or raise an exception.
        """
        for mimetype in self._get_accept_list():
            accept_mimetype = MimeType.parse(mimetype)
            for renderer in renderers:
                if accept_mimetype.match(renderer.mimetype):
                    return renderer, renderer.mimetype.replace(params=accept_mimetype.params)

        raise NotAcceptable()

    def _get_accept_list(self):
        """
        Given the incoming request, return a list of accepted media type strings.
        """
        header = request.environ.get('HTTP_ACCEPT') or '*/*'
        return [token.strip() for token in header.split(',')]
