from flask import Flask, request
from flask_webapi.exceptions import NotAcceptable, UnsupportedMediaType
from flask_webapi.negotiators import DefaultContentNegotiator
from flask_webapi.parsers import JSONParser
from flask_webapi.renderers import JSONRenderer
from flask_webapi.utils.mimetypes import MimeType
from unittest import TestCase


class TestSelectParser(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.negotiation = DefaultContentNegotiator()

    def test_empty_parsers(self):
        with self.app.test_request_context():
            with self.assertRaises(UnsupportedMediaType):
                self.negotiation.select_parser([])

    def test_empty_content_type(self):
        with self.app.test_request_context():
            with self.assertRaises(UnsupportedMediaType):
                self.negotiation.select_parser([JSONParser()])

    def test_valid_content_type(self):
        with self.app.test_request_context(content_type='application/json;charset=utf-8'):
            parsers = [JSONParser()]
            parser, mimetype = self.negotiation.select_parser(parsers)
            self.assertEqual(parser, parsers[0])
            self.assertEqual(mimetype, MimeType.parse(request.content_type))

    def test_invalid_content_type(self):
        with self.app.test_request_context(content_type='application/data'):
            with self.assertRaises(UnsupportedMediaType):
                self.negotiation.select_parser([JSONParser()])


class TestSelectRenderer(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.negotiation = DefaultContentNegotiator()

    def test_empty_renderers(self):
        with self.app.test_request_context():
            with self.assertRaises(NotAcceptable):
                self.negotiation.select_renderer([])

    def test_empty_accept_header(self):
        with self.app.test_request_context():
            renderers = [JSONRenderer(), JSONRenderer()]
            renderer, mimetype = self.negotiation.select_renderer(renderers)
            self.assertEqual(renderer, renderers[0])
            self.assertEqual(mimetype, renderers[0].mimetype)

    def test_valid_accept_header(self):
        with self.app.test_request_context(headers={'accept': 'application/json; indent=6'}):
            renderers = [JSONRenderer()]
            renderer, mimetype = self.negotiation.select_renderer(renderers)
            self.assertEqual(renderer, renderers[0])
            self.assertEqual(mimetype, MimeType.parse(request.headers['accept']))

    def test_invalid_accept_header(self):
        with self.app.test_request_context(headers={'accept': 'application/data'}):
            with self.assertRaises(NotAcceptable):
                self.negotiation.select_renderer([JSONParser()])

    def test_multiple_accept_header(self):
        with self.app.test_request_context(headers={'accept': 'application/xml,application/json;'}):
            renderers = [JSONRenderer()]
            renderer, mimetype = self.negotiation.select_renderer(renderers)
            self.assertEqual(renderer, renderers[0])
            self.assertEqual(str(mimetype), 'application/json')

    def test_any_in_accept_header(self):
        with self.app.test_request_context(headers={'accept': '*/*'}):
            renderers = [JSONRenderer()]
            renderer, mimetype = self.negotiation.select_renderer(renderers)
            self.assertEqual(renderer, renderers[0])
            self.assertEqual(str(mimetype), 'application/json')
