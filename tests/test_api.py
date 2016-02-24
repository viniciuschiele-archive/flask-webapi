import inspect

from flask import Flask
from flask_webapi import WebAPI, ControllerBase
from flask_webapi.decorators import route
from unittest import TestCase


class TestWebAPI(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.client = self.app.test_client()

    def test_add_controller_after_init_app(self):
        self.api = WebAPI()
        self.api.init_app(self.app)
        self.api.add_controller(Controller)

        response = self.client.get('/controller/action')
        self.assertEqual(response.status_code, 204)

    def test_add_controller_before_init_app(self):
        self.api = WebAPI()
        self.api.add_controller(Controller)
        self.api.init_app(self.app)

        response = self.client.get('/controller/action')
        self.assertEqual(response.status_code, 204)

    def test_import_controllers_with_module_path(self):
        self.api = WebAPI()
        self.api.import_controllers('tests.test_api')
        self.api.init_app(self.app)

        response = self.client.get('/controller/action')
        self.assertEqual(response.status_code, 204)

    def test_import_controllers_with_module_object(self):
        self.api = WebAPI()
        self.api.import_controllers(inspect.getmodule(TestWebAPI))
        self.api.init_app(self.app)

        response = self.client.get('/controller/action')
        self.assertEqual(response.status_code, 204)

        response = self.client.get('/controller/action2')
        self.assertEqual(response.status_code, 204)

    def test_import_controllers_from_config(self):
        self.app.config['WEBAPI_IMPORTS'] = ['tests.test_api']
        self.api = WebAPI()
        self.api.init_app(self.app)

        response = self.client.get('/controller/action')
        self.assertEqual(response.status_code, 204)

        response = self.client.get('/controller/action2')
        self.assertEqual(response.status_code, 204)


class Controller(ControllerBase):
    @route('/controller/action')
    def action(self):
        pass


@route('/controller/action2')
def action():
    pass
