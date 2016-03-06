from flask import Flask, json
from flask_webapi import WebAPI
from flask_webapi.decorators import content_negotiator, route
from flask_webapi.negotiation import DefaultContentNegotiator
from unittest import TestCase


class TestView(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.client = self.app.test_client()

    def test_single_mimetype_in_accept_header(self):
        @route('/view')
        @content_negotiator(DefaultContentNegotiator)
        def view():
            return {}

        self.api.add_view(view)
        response = self.client.get('/view', headers={'accept': 'application/json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'application/json')
        self.assertEqual(json.loads(response.get_data(as_text=True)), {})

    def test_multiple_mimetypes_in_accept_header(self):
        @route('/view')
        @content_negotiator(DefaultContentNegotiator)
        def view():
            return {}

        self.api.add_view(view)
        response = self.client.get('/view', headers={'accept': 'application/xml,application/json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'application/json')
        self.assertEqual(json.loads(response.get_data(as_text=True)), {})

    def test_empty_accept_header(self):
        @route('/view')
        @content_negotiator(DefaultContentNegotiator)
        def view():
            return {}

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'application/json')
        self.assertEqual(json.loads(response.get_data(as_text=True)), {})

    def test_not_supported_mimetype_in_accept_header(self):
        @route('/view')
        @content_negotiator(DefaultContentNegotiator)
        def view():
            return {}

        self.api.add_view(view)
        response = self.client.get('/view', headers={'accept': 'application/xml'})
        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.headers['content-type'], 'application/json')
        self.assertEqual(json.loads(response.get_data(as_text=True)),
                         dict(errors=[dict(message='Could not satisfy the request Accept header.')]))

    def test_star_in_accept_header(self):
        @route('/view')
        @content_negotiator(DefaultContentNegotiator)
        def view():
            return {}

        self.api.add_view(view)
        response = self.client.get('/view', headers={'accept': '*/*'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'application/json')
        self.assertEqual(json.loads(response.get_data(as_text=True)), {})
