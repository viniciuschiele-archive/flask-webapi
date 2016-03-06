from flask import Flask, json
from flask_webapi import WebAPI, serializers
from flask_webapi.decorators import params, route
from unittest import TestCase


class TestView(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.client = self.app.test_client()

    def test_query_param(self):
        @route('/view')
        @params({'name': serializers.StringField})
        def view(name):
            return {'name': name}
        self.api.add_view(view)
        response = self.client.get('/view?name=john')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(name='john'))

    def test_empty_query_param(self):
        @route('/view')
        @params({'name': serializers.StringField})
        def view(name):
            return {'name': name}
        self.api.add_view(view)
        response = self.client.get('/view?name=')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(name=None))

    def test_missing_query_param(self):
        @route('/view')
        @params({'name': serializers.StringField})
        def view(name):
            return {'name': name}
        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(name=None))
