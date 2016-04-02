"""
Parsers used to parse a stream into Python object.
"""

import pickle

from abc import ABCMeta, abstractmethod
from flask import json
from werkzeug.urls import url_decode_stream
from .exceptions import ParseError


class MimeType(object):
    """
    Represents a mimetype.
    """

    def __init__(self, main_type, sub_type, params=None):
        """
        Initializes a new instance of MimeType.

        :param str main_type: The first part of the mimetype before the slash.
        :param str sub_type: The second part of the mimetype after the slash.
        :param dict params: The parameters of the mimetype.
        """
        self.main_type = main_type
        self.sub_type = sub_type
        self.params = params

    def __eq__(self, other):
        """
        Compares the current MimeType against the given MimeType.
        :param MimeType other: The MimeType to be compared.
        :return: True if both MimeType are equals.
        """
        if other is None:
            return False

        return self.main_type == other.main_type and \
               self.sub_type == other.sub_type and \
               self.params == other.params

    def __str__(self):
        """
        Returns the string representation.
        :return: A string.
        """
        ret = self.main_type + '/' + self.sub_type
        for key, val in self.params.items():
            ret += '; ' + key + '=' + val
        return ret

    @classmethod
    def parse(cls, mimetype):
        """
        Extracts the full type and parameters from the given MimeType.

        :param str mimetype: The mimetype to be parsed.
        :return: Returns a tuple with full type and parameters.
        """
        plist = mimetype.split(';')

        main_type, _, sub_type = plist.pop(0).lower().strip().partition('/')
        params = {}

        for p in plist:
            kv = p.split('=')
            if len(kv) != 2:
                continue
            v = kv[1].strip()
            if v:
                params[kv[0].strip()] = v

        return MimeType(main_type, sub_type, params)

    def match(self, other):
        """
        Checks if the given MimeType matches to the this MimeType.

        :param MimeType other: The MimeType to compare to.
        :return bool: True if this MimeType matches the given MediaType.
        """
        if self.sub_type != '*' and other.sub_type != '*' and other.sub_type != self.sub_type:
            return False

        if self.main_type != '*' and other.main_type != '*' and other.main_type != self.main_type:
            return False

        return True

    def replace(self, main_type=None, sub_type=None, params=None):
        """
        Return a new MimeType with new values for the specified fields.
        :param str main_type: The new main type.
        :param str sub_type: The new sub type.
        :param dict params: The new parameters.
        :return: A new instance of MimeType
        """
        if main_type is None:
            main_type = self.main_type

        if sub_type is None:
            sub_type = self.sub_type

        if params is None:
            params = self.params

        return MimeType(main_type, sub_type, params)


class BaseInputFormatter(metaclass=ABCMeta):
    """
    A base class from which all parser classes should inherit.
    """

    mimetype = None

    @abstractmethod
    def read(self, request, mimetype):
        """
        Parses the given stream and returns a Python object.
        :param request: The request containing the data to be parsed.
        :param MimeType mimetype: The mimetype chose to parse the data.
        :return: A Python object
        """


class BaseOutputFormatter(metaclass=ABCMeta):
    """
    A base class from which all renderer classes should inherit.
    """

    mimetype = None

    @abstractmethod
    def write(self, response, data, mimetype=None):
        """
        Serializes the given data into a byte array.
        :param data: The data to be rendered.
        :param mimetype: The mimetype to render the data.
        :return: A byte array.
        """


class JsonInputFormatter(BaseInputFormatter):
    """
    Parses JSON data into Python object.
    """

    mimetype = MimeType.parse('application/json')

    def read(self, request, mimetype):
        """
        Parses a stream containing a JSON document and returns a Python object.
        :param request: The request containing the Json document.
        :param MimeType mimetype: The mimetype chose to parse the data.
        :return: A Python object.
        """
        encoding = mimetype.params.get('charset') or 'utf-8'

        try:
            return json.loads(request.get_data(), encoding=encoding)
        except ValueError as e:
            raise ParseError('Json parse error: ' + str(e))


class JsonOutputFormatter(BaseOutputFormatter):
    """
    Renderer which render into JSON.
    """

    mimetype = MimeType.parse('application/json')

    def write(self, response, data, mimetype=None):
        """
        Serializes the given data into a byte array containing a JSON document.
        :param data: A Python object.
        :param MimeType mimetype: The mimetype to render the data.
        :return: A byte array containing a JSON document.
        """
        if not mimetype:
            mimetype = self.mimetype

        indent = self.get_indent(mimetype)
        encoding = mimetype.params.get('charset') or 'utf-8'
        response.set_data(json.dumps(data, indent=indent).encode(encoding))
        response.content_type = str(mimetype)

    def get_indent(self, mimetype):
        """
        Gets the indent parameter from the mimetype.
        :param MimeType mimetype: The mimetype with parameters.
        :return int: The indent if found, otherwise none.
        """
        try:
            indent = max(int(mimetype.params.get('indent', '0')), 0)

            if indent == 0:
                return None

            return indent
        except ValueError:
            return None


class PickleOutputFormatter(BaseOutputFormatter):
    """
    Renderer which render into Pickle binary.
    """

    mimetype = MimeType.parse('application/pickle')

    def write(self, response, data, mimetype=None):
        """
        Serializes the given data into a Pickle byte array.
        :param data: A Python object.
        :param mimetype: The mimetype to render the data.
        :return: A byte array containing a Pickle document.
        """
        response.set_data(pickle.dumps(data))
        response.content_type = str(mimetype)


class FormInputFormatter(BaseInputFormatter):
    """
    Parses JSON data into Python object.
    """

    mimetype = MimeType.parse('application/x-www-form-urlencoded')

    def read(self, request, mimetype):
        """
        Parses a stream containing the form data and returns a Python object.
        :param request: The request containing a form data.
        :param MimeType mimetype: The mimetype chose to parse the data.
        :return: A Python object.
        """
        return request.form
