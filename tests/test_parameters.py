from flask import Flask, json
from flask_webapi import WebAPI, fields, schemas
from flask_webapi.decorators import param, route
from werkzeug.datastructures import Headers
from unittest import TestCase


class TestParam(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.debug = True
        self.api = WebAPI(self.app)
        self.client = self.app.test_client()

    def test_query_param_without_location(self):
        @route('/view')
        @param('param_1', fields.StringField)
        def view(param_1):
            return {'param_1': param_1}
        self.api.add_view(view)

        response = self.client.get('/view?param_1=123')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(param_1='123'))

    def test_form_param_without_location(self):
        @route('/view', methods=['POST'])
        @param('param_1', fields.StringField)
        def view(param_1):
            return {'param_1': param_1}
        self.api.add_view(view)

        response = self.client.post('/view', data=dict(param_1='123'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(param_1='123'))

    def test_body_param_without_location(self):
        class Schema(schemas.Schema):
            name = fields.StringField()
            age = fields.IntegerField()

        @route('/view', methods=['POST'])
        @param('param_1', Schema)
        def view(param_1):
            return param_1
        self.api.add_view(view)

        data = json.dumps(dict(name='myname', age=20))

        response = self.client.post('/view', data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(name='myname', age=20))

    def test_param_with_cookie_location(self):
        @route('/view')
        @param('param_1', fields.StringField, location='cookie')
        def view(param_1):
            return {'param_1': param_1}
        self.api.add_view(view)

        self.client.set_cookie('localhost', 'param_1', '123')
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(param_1='123'))

    def test_param_with_header_location(self):
        @route('/view')
        @param('param_1', fields.StringField, location='header')
        def view(param_1):
            return {'param_1': param_1}
        self.api.add_view(view)

        headers = Headers()
        headers.add('param_1', '123')
        response = self.client.get('/view', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(param_1='123'))

    def test_param_with_form_location(self):
        @route('/view', methods=['POST'])
        @param('param_1', fields.StringField, location='form')
        def view(param_1):
            return {'param_1': param_1}
        self.api.add_view(view)

        response = self.client.post('/view', data=dict(param_1='123'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(param_1='123'))

    def test_param_with_query_location(self):
        @route('/view')
        @param('param_1', fields.StringField, location='query')
        def view(param_1):
            return {'param_1': param_1}
        self.api.add_view(view)

        response = self.client.get('/view?param_1=123')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(param_1='123'))

    def test_param_with_body_location(self):
        class Schema(schemas.Schema):
            name = fields.StringField()
            age = fields.IntegerField()

        @route('/view', methods=['POST'])
        @param('param_1', Schema, location='body')
        def view(param_1):
            return param_1
        self.api.add_view(view)

        data = json.dumps(dict(name='myname', age=20))

        response = self.client.post('/view', data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(name='myname', age=20))

    def test_param_with_body_location_and_unsupported_content_type(self):
        class Schema(schemas.Schema):
            name = fields.StringField()
            age = fields.IntegerField()

        @route('/view', methods=['POST'])
        @param('param_1', Schema, location='body')
        def view(param_1):
            return param_1
        self.api.add_view(view)

        data = json.dumps(dict(name='myname', age=20))

        response = self.client.post('/view', data=data, content_type='application/data')
        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(json.loads(response.data),
                         {'errors': [{'message': 'Unsupported media type "application/data" in request.'}]})

    def test_param_with_body_location_and_malformed_data(self):
        class Schema(schemas.Schema):
            name = fields.StringField()
            age = fields.IntegerField()

        @route('/view', methods=['POST'])
        @param('param_1', Schema, location='body')
        def view(param_1):
            return param_1
        self.api.add_view(view)

        response = self.client.post('/view', data='invalid data', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_param_with_invalid_location(self):
        @route('/view')
        @param('param_1', fields.StringField, location='not_found')
        def view(param_1):
            return {'param_1': param_1}
        self.api.add_view(view)

        response = self.client.get('/view?param_1=123')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(json.loads(response.data),
                         {'errors': [{'message': 'Argument provider for location "not_found" not found.'}]})
