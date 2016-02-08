from flask import Flask, json
from flask_webapi import WebAPI, ViewBase, route
from flask_webapi.errors import ServerError
from werkzeug.exceptions import BadRequest
from unittest import TestCase


class TestView(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.api.add_view(View)
        self.api.add_view(ViewWithPrefix)
        self.api.add_view(action_without_view)
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

    def test_action_not_allowed(self):
        response = self.client.get('/action_not_allowed')
        self.assertEqual(response.status_code, 405)

    def test_action_with_no_return(self):
        response = self.client.get('/action_with_not_return')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b'')

    def test_action_without_view(self):
        response = self.client.get('/action_without_view')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b'')

    def test_view_with_prefix(self):
        response = self.client.get('/prefix/action')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b'')


class View(ViewBase):
    @route('/api_error')
    def api_error(self):
        raise ServerError(field='id')

    @route('/custom_error')
    def custom_error(self):
        raise Exception()

    @route('/http_error')
    def http_error(self):
        raise BadRequest()

    @route('/action_with_not_return')
    def action_with_not_return(self):
        pass

    @route('/action_not_allowed', methods=['POST'])
    def action_not_allowed(self):
        pass


@route('/prefix')
class ViewWithPrefix(ViewBase):
    @route('/action')
    def get(self):
        pass


@route('/action_without_view')
def action_without_view():
    pass
