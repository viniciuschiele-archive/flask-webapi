"""
Parsers used to parse a stream into Python object.
"""

from abc import ABCMeta, abstractmethod
from flask import json
from werkzeug.urls import url_decode_stream
from .exceptions import ParseError
from .utils.mimetypes import MimeType


class ParserBase(metaclass=ABCMeta):
    """
    Base class for all parsers.
    """

    mimetype = None

    @abstractmethod
    def parse(self, stream, mimetype):
        """
        Parses the given data and returns a Python object.
        :param stream: The stream containing the data to be parsed.
        :param mimetype: The mimetype to parse the data.
        :return: A Python object
        """


class JSONParser(ParserBase):
    """
    Parses JSON data into Python object.
    """

    mimetype = MimeType.parse('application/json')

    def parse(self, stream, mimetype):
        """
        Parses a stream containing a JSON document and returns a Python object.
        :param stream: The stream containing a JSON document.
        :param MimeType mimetype: The mimetype chose to parse the data.
        :return: A Python object.
        """
        encoding = mimetype.params.get('charset') or 'utf-8'

        try:
            return json.load(stream, encoding=encoding)
        except ValueError as e:
            raise ParseError('JSON parse error: ' + str(e))


class FormDataParser(ParserBase):
    """
    Parses JSON data into Python object.
    """

    mimetype = MimeType.parse('application/x-www-form-urlencoded')

    def parse(self, stream, mimetype):
        """
        Parses a stream containing the form data and returns a Python object.
        :param stream: The stream containing a form data.
        :param MimeType mimetype: The mimetype chose to parse the data.
        :return: A Python object.
        """
        encoding = mimetype.params.get('charset') or 'utf-8'

        return url_decode_stream(stream, encoding)
