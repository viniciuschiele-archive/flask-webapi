from flask import Flask
from flask_webapi import WebAPI
from flask_webapi.routers import route
from unittest import TestCase


class TestWebAPI(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI()
        self.client = self.app.test_client()

    def test_add_view_after_init_app(self):
        self.api.init_app(self.app)
        self.api.add_view(FakeView)
        self.api.add_view(view_func)

        response = self.client.get('/view')
        self.assertEqual(response.status_code, 204)

        response = self.client.get('/view_func')
        self.assertEqual(response.status_code, 204)

    def test_add_view_before_init_app(self):
        self.api.add_view(FakeView)
        self.api.add_view(view_func)
        self.api.init_app(self.app)

        response = self.client.get('/view')
        self.assertEqual(response.status_code, 204)

        response = self.client.get('/view_func')
        self.assertEqual(response.status_code, 204)

    def test_add_invalid_view(self):
        attr_view = ''

        with self.assertRaises(TypeError):
            self.api.add_view(attr_view)

    def test_add_same_view_multiple_times(self):
        self.api.add_view(FakeView)
        self.api.add_view(FakeView)

        with self.assertRaises(AssertionError):
            self.api.init_app(self.app)

    def test_scan_views_with_string_package(self):
        self.api.scan_views('tests', 'test_api')
        self.api.init_app(self.app)

        response = self.client.get('/view')
        self.assertEqual(response.status_code, 204)

        response = self.client.get('/view_func')
        self.assertEqual(response.status_code, 204)

    def test_scan_views_with_list_package(self):
        self.api.scan_views(['tests'], 'test_api')
        self.api.init_app(self.app)

        response = self.client.get('/view')
        self.assertEqual(response.status_code, 204)

        response = self.client.get('/view_func')
        self.assertEqual(response.status_code, 204)

    def test_scan_views_with_invalid_module(self):
        with self.assertRaises(ImportError):
            self.api.scan_views('tests', 'module_not_found')


class FakeView(object):
    @route('/view')
    def view(self):
        pass


@route('/view_func')
def view_func():
    pass
