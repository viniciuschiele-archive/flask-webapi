import inspect

from flask import Flask
from flask_webapi import WebAPI, ViewBase
from flask_webapi.decorators import route
from unittest import TestCase


class TestWebAPI(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.client = self.app.test_client()

    def test_add_view_after_init_app(self):
        self.api = WebAPI()
        self.api.init_app(self.app)
        self.api.add_view(View)

        response = self.client.get('/view/action')
        self.assertEqual(response.status_code, 204)

    def test_add_view_before_init_app(self):
        self.api = WebAPI()
        self.api.add_view(View)
        self.api.init_app(self.app)

        response = self.client.get('/view/action')
        self.assertEqual(response.status_code, 204)

    def test_scan_path(self):
        self.api = WebAPI()
        self.api.scan('tests.test_api')
        self.api.init_app(self.app)

        response = self.client.get('/view/action')
        self.assertEqual(response.status_code, 204)

    def test_scan_module(self):
        self.api = WebAPI()
        self.api.scan(inspect.getmodule(TestWebAPI))
        self.api.init_app(self.app)

        response = self.client.get('/view/action')
        self.assertEqual(response.status_code, 204)

        response = self.client.get('/view/action2')
        self.assertEqual(response.status_code, 204)

    def test_scan_from_config(self):
        self.app.config['WEBAPI_IMPORTS'] = ['tests.test_api']
        self.api = WebAPI()
        self.api.init_app(self.app)

        response = self.client.get('/view/action')
        self.assertEqual(response.status_code, 204)

        response = self.client.get('/view/action2')
        self.assertEqual(response.status_code, 204)


class View(ViewBase):
    @route('/view/action')
    def action(self):
        pass


@route('/view/action2')
def action():
    pass
