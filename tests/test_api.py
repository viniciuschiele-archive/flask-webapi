import inspect

from flask import Flask
from flask_webapi import WebAPI, BaseView
from flask_webapi.decorators import route
from unittest import TestCase


class TestWebAPI(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI()
        self.client = self.app.test_client()

    def test_add_view_after_init_app(self):
        self.api.init_app(self.app)
        self.api.add_view(View)
        self.api.add_view(view_func)

        response = self.client.get('/view')
        self.assertEqual(response.status_code, 204)

        response = self.client.get('/view_func')
        self.assertEqual(response.status_code, 204)

    def test_add_view_before_init_app(self):
        self.api.add_view(View)
        self.api.add_view(view_func)
        self.api.init_app(self.app)

        response = self.client.get('/view')
        self.assertEqual(response.status_code, 204)

        response = self.client.get('/view_func')
        self.assertEqual(response.status_code, 204)

    def test_add_invalid_view(self):
        attr_view = None

        def invalid_view():
            pass

        class InvalidView(object):
            pass

        with self.assertRaises(TypeError):
            self.api.add_view(attr_view)

        with self.assertRaises(TypeError):
            self.api.add_view(invalid_view)

        with self.assertRaises(TypeError):
            self.api.add_view(InvalidView)

    def test_scan_views_from_path(self):
        self.api.scan('tests.test_api')
        self.api.init_app(self.app)

        response = self.client.get('/view')
        self.assertEqual(response.status_code, 204)

        response = self.client.get('/view_func')
        self.assertEqual(response.status_code, 204)

    def test_scan_views_from_module(self):
        self.api.scan(inspect.getmodule(TestWebAPI))
        self.api.init_app(self.app)

        response = self.client.get('/view')
        self.assertEqual(response.status_code, 204)

        response = self.client.get('/view_func')
        self.assertEqual(response.status_code, 204)

    def test_scan_views_from_config(self):
        self.app.config['WEBAPI_IMPORTS'] = ['tests.test_api']
        self.api.init_app(self.app)

        response = self.client.get('/view')
        self.assertEqual(response.status_code, 204)

        response = self.client.get('/view_func')
        self.assertEqual(response.status_code, 204)


class View(BaseView):
    @route('/view')
    def view(self):
        pass


@route('/view_func')
def view_func():
    pass
