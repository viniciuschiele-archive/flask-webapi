"""
Provides a set of formatters to read and write content from/to the request/response body.
"""

import pickle

from abc import ABCMeta, abstractmethod
from flask import json
from .utils.mimetypes import MimeType


def get_default_input_formatters():
    """
    Gets all instances of input formatters.
    :return: A list of input formatters.
    """
    return [JsonInputFormatter(), FormInputFormatter()]


def get_default_output_formatters():
    """
    Gets all instances of output formatters.
    :return: A list of output formatters.
    """
    return [JsonOutputFormatter()]


class InputFormatter(metaclass=ABCMeta):
    """
    A base class from which all input formatter classes should inherit.
    """

    mimetype = None

    @abstractmethod
    def read(self, request, mimetype=None):
        """
        Reads a `dict` object from the request body.
        :param request: The request containing the data.
        :param MimeType mimetype: The mimetype chose to read the data.
        :return: A `dict` instance.
        """


class OutputFormatter(metaclass=ABCMeta):
    """
    A base class from which all output formatter classes should inherit.
    """

    mimetype = None

    @abstractmethod
    def write(self, response, data, mimetype=None):
        """
        Writes the given data into response body.
        :param response: The flask response instance.
        :param data: The data to be written into body.
        :param MimeType mimetype: The content type.
        """


class FormInputFormatter(InputFormatter):
    """
    An `InputFormatter` for form urlencoded content.
    """

    mimetype = MimeType.parse('application/x-www-form-urlencoded')

    def read(self, request, mimetype=None):
        """
        Reads a `dict` object from the request body..
        :param request: The request containing the data.
        :param MimeType mimetype: The mimetype chose to read the data.
        :return: A `dict` instance.
        """
        return request.form


class JsonInputFormatter(InputFormatter):
    """
    An `InputFormatter` for JSON content.
    """

    mimetype = MimeType.parse('application/json')

    def read(self, request, mimetype=None):
        """
        Reads a `dict` object from the request body.
        :param request: The request containing the data.
        :param MimeType mimetype: The mimetype chose to read the data.
        :return: A `dict` instance.
        """
        if not mimetype:
            mimetype = self.mimetype

        encoding = mimetype.params.get('charset', 'utf-8')
        return json.loads(request.get_data(), encoding=encoding)


class JsonOutputFormatter(OutputFormatter):
    """
    An `OutputFormatter` for JSON content.
    """

    mimetype = MimeType.parse('application/json')

    def write(self, response, data, mimetype=None):
        """
        Writes the given data into response body.
        :param response: The flask response instance.
        :param data: The data to be written into body.
        :param MimeType mimetype: The content type.
        """
        if not mimetype:
            mimetype = self.mimetype

        indent = self.get_indent(mimetype)
        encoding = mimetype.params.get('charset', 'utf-8')
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


class PickleInputFormatter(InputFormatter):
    """
    An `InputFormatter` for JSON content.
    """

    mimetype = MimeType.parse('application/pickle')

    def read(self, request, mimetype=None):
        """
        Reads a `dict` object from the request body.
        :param request: The request containing the data.
        :param MimeType mimetype: The mimetype chose to read the data.
        :return: A `dict` instance.
        """
        if not mimetype:
            mimetype = self.mimetype

        encoding = mimetype.params.get('charset', 'ASCII')
        return pickle.loads(request.get_data(), encoding=encoding)


class PickleOutputFormatter(OutputFormatter):
    """
    An `OutputFormatter` for Pickle content.
    """

    mimetype = MimeType.parse('application/pickle')

    def write(self, response, data, mimetype=None):
        """
        Writes the given data into response body.
        :param response: The flask response instance.
        :param data: The data to be written into body.
        :param MimeType mimetype: The content type.
        """
        if not mimetype:
            mimetype = self.mimetype

        response.set_data(pickle.dumps(data))
        response.content_type = str(mimetype)
