"""
Content negotiation selects a appropriated parser and renderer for a HTTP request.
"""

from abc import ABCMeta, abstractmethod
from flask import request
from .errors import NotAcceptable
from .mimetypes import MimeType


def perform_content_negotiation(force=False):
    """
    Determine which parser and renderer to be used to parse the incoming request
    and to render the response.

    :param force: True to select the first parser/renderer when the appropriated is not found.
    """
    action = request.action

    negotiator = action.get_content_negotiator()
    renderers = action.get_renderers()

    renderer_pair = negotiator.select_renderer(renderers)

    if renderer_pair is None:
        if not force:
            raise NotAcceptable()

        renderer_pair = renderers[0], renderers[0].mimetype

    request.accepted_renderer, request.accepted_mimetype = renderer_pair


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
        pass

    @abstractmethod
    def select_renderer(self, renderers):
        """
        Selects the appropriated renderer for the given request.
        :param renderers: The lists of renderers.
        :return: The renderer selected or none.
        """
        pass


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
                return parser, mimetype

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
                    return renderer, accept_mimetype

        return None
