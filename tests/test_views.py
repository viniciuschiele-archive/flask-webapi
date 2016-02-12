from flask import Flask, json
from flask_webapi import WebAPI, ViewBase, route

from unittest import TestCase


class TestViews(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.api.add_view(View)
        self.api.add_view(ViewWithPrefix)
        self.api.add_view(action_without_view)
        self.client = self.app.test_client()

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

    def test_action_returning_headers(self):
        response = self.client.get('/action_returning_headers')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b'')
        self.assertEqual(response.headers['my_header'], 'value1')

    def test_action_returning_status_code(self):
        response = self.client.get('/action_returning_status_code')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, b'')


class View(ViewBase):
    @route('/action_with_not_return')
    def action_with_not_return(self):
        pass

    @route('/action_not_allowed', methods=['POST'])
    def action_not_allowed(self):
        pass

    @route('/action_returning_headers')
    def action_returning_headers(self):
        return None, None, {'my_header': 'value1'}

    @route('/action_returning_status_code')
    def action_returning_status_code(self):
        return None, 201


@route('/prefix')
class ViewWithPrefix(ViewBase):
    @route('/action')
    def get(self):
        pass


@route('/action_without_view')
def action_without_view():
    pass
