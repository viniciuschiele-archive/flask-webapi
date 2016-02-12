from flask import Flask, json, Response
from flask_webapi import WebAPI, ControllerBase, route
from flask_webapi.decorators import error_handler
from flask_webapi.errors import ServerError
from werkzeug.exceptions import BadRequest
from unittest import TestCase


class TestController(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.api.add_controller(Controller)
        self.client = self.app.test_client()

    def test_api_error(self):
        response = self.client.get('/api_error')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(json.loads(response.get_data(as_text=True)),
                         dict(errors=[dict(message='A server error occurred.', field='id')]))

    def test_custom_error(self):
        response = self.client.get('/custom_error')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(json.loads(response.get_data(as_text=True)),
                         dict(errors=[dict(message='A server error occurred.')]))

    def test_http_error(self):
        response = self.client.get('/http_error')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.get_data(as_text=True)),
                         dict(errors=[dict(message=BadRequest.description)]))

    def test_customer_error_handler(self):
        response = self.client.get('/custom_error_handler')
        self.assertEqual(response.status_code, 500)
        self.assertEqual('A server error occurred.', response.get_data(as_text=True))


def app_error_handler(error):
    return Response(str(error), status=500)


class Controller(ControllerBase):
    @route('/api_error')
    def api_error(self):
        raise ServerError(field='id')

    @route('/custom_error')
    def custom_error(self):
        raise Exception()

    @route('/http_error')
    def http_error(self):
        raise BadRequest()

    @route('/custom_error_handler')
    @error_handler(app_error_handler)
    def custom_error_handler(self):
        raise ServerError()
