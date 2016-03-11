import pickle

from flask import Flask, json
from flask_webapi import WebAPI
from flask_webapi.decorators import route, renderer
from flask_webapi.renderers import RendererBase, JSONRenderer, PickleRenderer
from flask_webapi.utils.mimetypes import MimeType
from unittest import TestCase


class TestRenderer(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.client = self.app.test_client()

        class RendererA(RendererBase):
            mimetype = MimeType.parse('application/renderera')

            def render(self, data, mimetype):
                return 'RendererA'.encode()

        class RendererB(RendererBase):
            mimetype = MimeType.parse('application/rendererb')

            def render(self, data, mimetype):
                return 'RendererB'.encode()

        @route('/view')
        @renderer(RendererA, RendererB)
        def view():
            return 'text'

        self.api.add_view(view)

    def test_renderer_with_accept_empty(self):
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/renderera')
        self.assertEqual(response.data.decode(), 'RendererA')

    def test_renderer_with_accept_specified(self):
        response = self.client.get('/view', headers=dict(accept='application/rendererb'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/rendererb')
        self.assertEqual(response.data.decode(), 'RendererB')

    def test_renderer_with_accept_any(self):
        response = self.client.get('/view', headers=dict(accept='*/*'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/renderera')
        self.assertEqual(response.data.decode(), 'RendererA')

    def test_renderer_with_accept_unsupported(self):
        response = self.client.get('/view', headers=dict(accept='application/renderer'))
        self.assertEqual(response.status_code, 406)


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
