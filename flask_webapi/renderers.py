"""
Renderers used to render a Python object into byte array.
"""

import simplejson
import pickle

from abc import ABCMeta, abstractmethod
from .mimetypes import MimeType


class RendererBase(metaclass=ABCMeta):
    """
    Base class for all renderers.
    """

    mimetype = None

    @abstractmethod
    def render(self, data, mimetype):
        """
        Render the given data into JSON and returns a byte array.
        :param data: The data to be rendered.
        :param mimetype: The mimetype to render the data.
        :return: A byte array.
        """


class JSONRenderer(RendererBase):
    """
    Renderer which render into JSON.
    """

    mimetype = MimeType('application/json')

    def render(self, data, mimetype):
        """
        Serializes a Python object into a byte array containing a JSON document.

        :param data: A Python object.
        :param mimetype: The mimetype to render the data.
        :return: A byte array containing a JSON document.
        """

        indent = self.get_indent(mimetype)
        encoding = mimetype.params.get('charset') or 'utf-8'
        return simplejson.dumps(data, indent=indent).encode(encoding)

    def get_indent(self, mimetype):
        """
        Gets the indent parameter from the mimetype.

        :param MimeType mimetype: The mimetype with parameters.
        :return int: The indent if found, otherwise none.
        """
        indent = max(int(mimetype.params.get('indent', '0')), 0)

        if indent == 0:
            return None

        return indent


class PickleRenderer(RendererBase):
    """
    Renderer which render into Pickle binary.
    """

    mimetype = MimeType('application/pickle')

    def render(self, data, mimetype):
        """
        Serializes a Python object into a Pickle byte array.

        :param data: A Python object.
        :param mimetype: The mimetype to render the data.
        :return: A byte array containing a Pickle document.
        """

        return pickle.dumps(data)
