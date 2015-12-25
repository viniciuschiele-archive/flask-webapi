from flask import Flask
from flask_webapi import WebAPI, APIView, renderer, route
from flask_webapi.renderers import PickleRenderer
from unittest import TestCase


class TestRenderer(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.api.load_module('tests.test_renderers')
        self.client = self.app.test_client()

    def test_pickle_renderer(self):
        response = self.client.post('/add')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'application/pickle')


class BasicView(APIView):
    @route('/add', methods=['POST'])
    @renderer(PickleRenderer)
    def add(self):
        return {}
