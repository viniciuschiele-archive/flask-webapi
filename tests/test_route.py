from flask import Flask
from flask_webapi import WebAPI, APIView, route
from unittest import TestCase


class TestRoute(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.api.load_module('tests.test_route')
        self.client = self.app.test_client()

    def test_204_response(self):
        response = self.client.post('/view')
        self.assertEqual(response.status_code, 204)

    def test_404_response(self):
        response = self.client.post('/view_not_found')
        self.assertEqual(response.status_code, 404)

    def test_405_response(self):
        response = self.client.put('/view')
        self.assertEqual(response.status_code, 405)


class BasicView(APIView):
    @route('/view', methods=['POST'])
    def get(self):
        pass
