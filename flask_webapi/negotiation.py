"""
Content negotiation selects a appropriated parser and renderer for a HTTP request.
"""

from abc import ABCMeta, abstractmethod
from flask import request
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
        :return: The parser selected or none.
        """

    @abstractmethod
    def select_renderer(self, renderers):
        """
        Selects the appropriated renderer for the given request.
        :param renderers: The lists of renderers.
        :return: The renderer selected or none.
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
        :return: The parser selected or none.
        """

        if not request.content_type:
            return parsers[0], parsers[0].mimetype

        mimetype = MimeType(request.content_type)

        for parser in parsers:
            if mimetype.match(parser.mimetype):
                return parser

        return None

    def select_renderer(self, renderers):
        """
        Selects the appropriated parser which matches to the request's accept.
        :param renderers: The lists of parsers.
        :return: The parser selected or none.
        """

        if not len(request.accept_mimetypes):
            return renderers[0], renderers[0].mimetype

        for mimetype, quality in request.accept_mimetypes:
            accept_mimetype = MimeType(mimetype)
            for renderer in renderers:
                if accept_mimetype.match(renderer.mimetype):
                    return renderer, renderer.mimetype

        return None
