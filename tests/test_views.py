from flask import Flask
from flask_webapi import WebAPI
from flask_webapi.views import View
from flask_webapi.decorators import route
from unittest import TestCase


class TestView(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.client = self.app.test_client()

    def test_view_not_allowed(self):
        @route('/view', methods=['POST'])
        def view():
            pass
        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 405)

    def test_view_with_no_return(self):
        @route('/view')
        def view():
            pass
        self.api.add_view(view)

        response = self.client.get('/view')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b'')

    def test_view_returning_status_code(self):
        @route('/view')
        def view():
            return None, 201
        self.api.add_view(view)

        response = self.client.get('/view')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, b'')

    def test_view_returning_headers(self):
        @route('/view')
        def view():
            return None, None, {'my_header': 'value1'}
        self.api.add_view(view)

        response = self.client.get('/view')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b'')
        self.assertEqual(response.headers['my_header'], 'value1')

    def test_class_based_view_with_prefix(self):
        @route('/prefix')
        class FakeView(View):
            @route('/view')
            def get(self):
                pass
        self.api.add_view(FakeView)

        response = self.client.get('/prefix/view')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b'')
