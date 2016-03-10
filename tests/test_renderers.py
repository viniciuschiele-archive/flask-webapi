import pickle

from flask import json
from flask_webapi.renderers import JSONRenderer, PickleRenderer
from flask_webapi.utils.mimetypes import MimeType
from unittest import TestCase


class TestJSONRenderer(TestCase):
    def setUp(self):
        self.renderer = JSONRenderer()

    def test_indent_present(self):
        self.assertEqual(self.renderer.get_indent(MimeType.parse('application/json;indent=10')), 10)

    def test_indent_not_present(self):
        self.assertEqual(self.renderer.get_indent(MimeType.parse('application/json')), None)

    def test_min_indent(self):
        self.assertEqual(self.renderer.get_indent(MimeType.parse('application/json;indent=-1')), None)

    def test_invalid_indent(self):
        self.assertEqual(self.renderer.get_indent(MimeType.parse('application/json;indent=a')), None)

    def test_render(self):
        data = dict(field='value')
        mimetype = MimeType.parse('application/json')
        self.assertEqual(self.renderer.render(data, mimetype), b'{"field": "value"}')
        self.assertEqual(json.loads(self.renderer.render(data, mimetype)), data)


class TestPickleRenderer(TestCase):
    def setUp(self):
        self.renderer = PickleRenderer()

    def test_render(self):
        data = dict(field='value')
        mimetype = MimeType.parse('application/pickle')
        self.assertEqual(self.renderer.render(data, mimetype), b'\x80\x03}q\x00X\x05\x00\x00\x00fieldq\x01X\x05\x00\x00\x00valueq\x02s.')
        self.assertEqual(pickle.loads(self.renderer.render(data, mimetype)), data)
