from flask import Flask, json
from flask_webapi import WebAPI, fields, schemas
from flask_webapi.serialization import serializer
from flask_webapi.views import route
from unittest import TestCase


class TestView(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.client = self.app.test_client()

    def test_single_result_with_many_none(self):
        class Schema(schemas.Schema):
            field = fields.StringField()

        @route('/view')
        @serializer(Schema)
        def view():
            return {'field': 'value'}

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {'field': 'value'})

    def test_single_result_with_many_false(self):
        class Schema(schemas.Schema):
            field = fields.StringField()

        @route('/view')
        @serializer(Schema, many=False)
        def view():
            return {'field': 'value'}

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(field='value'))

    def test_multiple_results_with_many_none(self):
        class Schema(schemas.Schema):
            field = fields.StringField()

        @route('/view')
        @serializer(Schema)
        def view():
            return [{'field': 'value'}]

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), [dict(field='value')])

    def test_multiple_results_with_many_true(self):
        class Schema(schemas.Schema):
            field = fields.StringField()

        @route('/view')
        @serializer(Schema, many=True)
        def view():
            return [{'field': 'value'}]

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), [dict(field='value')])

    def test_multiple_results_with_envelope(self):
        class Schema(schemas.Schema):
            field = fields.StringField()

        @route('/view')
        @serializer(Schema, many=True, envelope='results')
        def view():
            return [{'field': 'value'}]

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(results=[dict(field='value')]))

    def test_none_with_envelope(self):
        class Schema(schemas.Schema):
            field = fields.StringField()

        @route('/view')
        @serializer(Schema, envelope='results')
        def view():
            return None

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b'')

    def test_fields_parameter(self):
        class Schema(schemas.Schema):
            first_name = fields.StringField()
            last_name = fields.StringField()
            age = fields.IntegerField()

        @route('/view')
        @serializer(Schema)
        def view():
            return {'first_name': 'foo',
                    'last_name': 'bar',
                    'age': 30}

        self.api.add_view(view)
        response = self.client.get('/view?fields=last_name')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {'last_name': 'bar'})

    def test_fields_parameter_with_empty_value(self):
        class Schema(schemas.Schema):
            first_name = fields.StringField()
            last_name = fields.StringField()
            age = fields.IntegerField()

        @route('/view')
        @serializer(Schema)
        def view():
            return {'first_name': 'foo',
                    'last_name': 'bar',
                    'age': 30}

        self.api.add_view(view)
        response = self.client.get('/view?fields=')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {'first_name': 'foo', 'last_name': 'bar', 'age': 30})

    def test_fields_parameter_with_invalid_field_name(self):
        class Schema(schemas.Schema):
            first_name = fields.StringField()
            last_name = fields.StringField()
            age = fields.IntegerField()

        @route('/view')
        @serializer(Schema)
        def view():
            return {'first_name': 'foo',
                    'last_name': 'bar',
                    'age': 30}

        self.api.add_view(view)
        response = self.client.get('/view?fields=password')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {})
