"""
Renderers used to render a Python object into byte array.
"""

import pickle

from abc import ABCMeta, abstractmethod
from flask import json
from .utils.mimetypes import MimeType


class BaseRenderer(metaclass=ABCMeta):
    """
    A base class from which all renderer classes should inherit.
    """

    mimetype = None

    @abstractmethod
    def render(self, data, mimetype):
        """
        Serializes the given data into a byte array.
        :param data: The data to be rendered.
        :param mimetype: The mimetype to render the data.
        :return: A byte array.
        """


class JSONRenderer(BaseRenderer):
    """
    Renderer which render into JSON.
    """

    mimetype = MimeType.parse('application/json')

    def render(self, data, mimetype):
        """
        Serializes the given data into a byte array containing a JSON document.
        :param data: A Python object.
        :param MimeType mimetype: The mimetype to render the data.
        :return: A byte array containing a JSON document.
        """
        indent = self.get_indent(mimetype)
        encoding = mimetype.params.get('charset') or 'utf-8'
        return json.dumps(data, indent=indent).encode(encoding)

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


class PickleRenderer(BaseRenderer):
    """
    Renderer which render into Pickle binary.
    """

    mimetype = MimeType.parse('application/pickle')

    def render(self, data, mimetype):
        """
        Serializes the given data into a Pickle byte array.
        :param data: A Python object.
        :param mimetype: The mimetype to render the data.
        :return: A byte array containing a Pickle document.
        """
        return pickle.dumps(data)
