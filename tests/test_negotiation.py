from flask import Flask
from flask_webapi import WebAPI, ViewBase
from flask_webapi.decorators import content_negotiator, route
from flask_webapi.negotiation import DefaultContentNegotiator
from unittest import TestCase


class TestDefaultContentNegotiator(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.api.add_view(View)
        self.client = self.app.test_client()

    def test_single_mimetype_in_accept_header(self):
        response = self.client.post('/add', headers={'accept': 'application/json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'application/json')

    def test_multiple_mimetypes_in_accept_header(self):
        response = self.client.post('/add', headers={'accept': 'application/xml,application/json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'application/json')

    def test_without_accept_header(self):
        response = self.client.post('/add')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'application/json')

    def test_not_supported_mimetype_in_accept_header(self):
        response = self.client.post('/add', headers={'accept': 'application/xml'})
        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.headers['content-type'], 'application/json')


class View(ViewBase):
    @route('/add', methods=['POST'])
    @content_negotiator(DefaultContentNegotiator)
    def add(self):
        return {}
