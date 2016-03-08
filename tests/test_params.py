from flask import Flask, json
from flask_webapi import WebAPI, serializers
from flask_webapi.decorators import param, route
from unittest import TestCase


class TestQueryString(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.client = self.app.test_client()

    def test_empty_param(self):
        @route('/view')
        @param('field', serializers.StringField(location='query'))
        def view(field):
            return {'field': field}
        self.api.add_view(view)
        response = self.client.get('/view?param=')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(field=None))

    def test_missing_param(self):
        @route('/view')
        @param('field', serializers.StringField(location='query'))
        def view(field):
            return {'field': field}
        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(field=None))

    def test_valid_param(self):
        @route('/view')
        @param('field', serializers.StringField(location='query'))
        def view(field):
            return {'field': field}
        self.api.add_view(view)
        response = self.client.get('/view?field=value')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(field='value'))

    def test_invalid_param(self):
        @route('/view')
        @param('field', serializers.IntegerField(location='query'))
        def view(field):
            pass
        self.api.add_view(view)
        response = self.client.get('/view?field=a')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.data),
                         dict(errors=[dict(message='A valid integer is required.', field='field')]))

    def test_list_param(self):
        @route('/view')
        @param('field', serializers.ListField(serializers.IntegerField, location='query'))
        def view(field):
            return {'field': field}
        self.api.add_view(view)
        response = self.client.get('/view?field=1&field=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(field=[1, 2]))

    def test_empty_list_param(self):
        @route('/view')
        @param('field', serializers.ListField(serializers.IntegerField, location='query'))
        def view(field):
            return {'field': field}

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(field=None))

    def test_multiple_params_with_serializer(self):
        class Serializer(serializers.Serializer):
            field1 = serializers.StringField
            field2 = serializers.IntegerField

        @route('/view')
        @param('fields', Serializer(location='query'))
        def view(fields):
            return {'field1': fields['field1'], 'field2': fields['field2']}

        self.api.add_view(view)
        response = self.client.get('/view?field1=a&field2=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(field1='a', field2=1))
