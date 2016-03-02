from flask import Flask, json
from flask_webapi import WebAPI, ControllerBase, serializers
from flask_webapi.decorators import params, route
from unittest import TestCase


class TestController(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.api.add_controller(Controller)
        self.client = self.app.test_client()

    def test_query_param(self):
        response = self.client.get('/action?name=john')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(name='john'))

    def test_empty_query_param(self):
        response = self.client.get('/action?name=')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(name=None))

    def test_missing_query_param(self):
        response = self.client.get('/action')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(name=None))


class Controller(ControllerBase):
    @route('/action')
    @params({'name': serializers.StringField})
    def action(self, name):
        return {'name': name}

