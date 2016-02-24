import pickle

from flask import Flask, json
from flask_webapi import WebAPI, ControllerBase
from flask_webapi.decorators import renderer, route
from flask_webapi.mimetypes import MimeType
from flask_webapi.renderers import JSONRenderer, PickleRenderer
from unittest import TestCase


class TestJSONRenderer(TestCase):
    def setUp(self):
        self.renderer = JSONRenderer()

    def test_indent_present(self):
        self.assertEqual(self.renderer.get_indent(MimeType('application/json;indent=10')), 10)

    def test_indent_not_present(self):
        self.assertEqual(self.renderer.get_indent(MimeType('application/json')), None)

    def test_min_indent(self):
        self.assertEqual(self.renderer.get_indent(MimeType('application/json;indent=-1')), None)

    def test_invalid_indent(self):
        self.assertEqual(self.renderer.get_indent(MimeType('application/json;indent=a')), None)

    def test_render(self):
        data = dict(field='value')
        mimetype = MimeType('application/json')
        self.assertEqual(self.renderer.render(data, mimetype), b'{"field": "value"}')
        self.assertEqual(json.loads(self.renderer.render(data, mimetype)), data)


class TestPickleRenderer(TestCase):
    def setUp(self):
        self.renderer = PickleRenderer()

    def test_render(self):
        data = dict(field='value')
        mimetype = MimeType('application/pickle')
        self.assertEqual(self.renderer.render(data, mimetype), b'\x80\x03}q\x00X\x05\x00\x00\x00fieldq\x01X\x05\x00\x00\x00valueq\x02s.')
        self.assertEqual(pickle.loads(self.renderer.render(data, mimetype)), data)


class TestController(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.api.add_controller(Controller)
        self.client = self.app.test_client()

    def test_content_type(self):
        response = self.client.get('/add')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'application/pickle')
        self.assertEqual(pickle.loads(response.data), dict(field='value'))


class Controller(ControllerBase):
    @route('/add')
    @renderer(PickleRenderer)
    def add(self):
        return dict(field='value')
