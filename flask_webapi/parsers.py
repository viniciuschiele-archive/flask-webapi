"""
Parsers used to parse a byte array into Python object.
"""

from abc import ABCMeta, abstractmethod
from flask import json, request
from .exceptions import ParseError, UnsupportedMediaType
from .utils.mimetypes import MimeType


def build_locations():
    return {
        'header': lambda context: request.headers,
        'form': lambda context: request.form,
        'query': lambda context: request.args,
        'body': parse_body
    }


def parse_body(context):
    negotiator = context.get_content_negotiator()
    parsers = context.get_parsers()

    parser_pair = negotiator.select_parser(parsers)

    if not parser_pair:
        raise UnsupportedMediaType(request.content_type)

    parser, mimetype = parser_pair

    try:
        return parser.parse(request.data, mimetype)
    except:
        raise ParseError()


class ParserBase(metaclass=ABCMeta):
    """
    Base class for all parsers.
    """

    mimetype = None

    @abstractmethod
    def parse(self, data, mimetype):
        """
        Parses the given data and returns a Python object.
        :param data: The data to be parsed.
        :param mimetype: The mimetype to parse the data.
        :return: A Python object
        """
        pass


class JSONParser(ParserBase):
    """
    Parses JSON data into Python object.
    """

    mimetype = MimeType.parse('application/json')

    def parse(self, data, mimetype):
        """
        Parses a byte array containing a JSON document and returns a Python object.
        :param data: The byte array containing a JSON document.
        :param MimeType mimetype: The mimetype chose to parse the data.
        :return: A Python object.
        """
        encoding = mimetype.params.get('charset') or 'utf-8'

        return json.loads(data.decode(encoding))
