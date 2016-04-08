from flask import Flask, json
from flask_webapi import WebAPI, serialization
from flask_webapi.parameters import param
from flask_webapi.routers import route
from werkzeug.datastructures import Headers
from unittest import TestCase


class TestLocation(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.debug = True
        self.api = WebAPI(self.app)
        self.client = self.app.test_client()

    def test_cookie_location(self):
        @route('/view')
        @param('name', serialization.StringField, location='cookie')
        def view(name):
            return {'name': name}
        self.api.add_view(view)

        self.client.set_cookie('localhost', 'name', 'foo')
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {'name': 'foo'})

    def test_header_location(self):
        @route('/view')
        @param('name', serialization.StringField(load_from='Name'), location='header')
        def view(name):
            return {'name': name}
        self.api.add_view(view)

        headers = Headers()
        headers.add('name', 'foo')
        response = self.client.get('/view', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {'name': 'foo'})

    def test_form_location(self):
        @route('/view', methods=['POST'])
        @param('name', serialization.StringField, location='form')
        def view(name):
            return {'name': name}
        self.api.add_view(view)

        response = self.client.post('/view', data={'name': 'foo'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {'name': 'foo'})

    def test_query_location(self):
        @route('/view')
        @param('name', serialization.StringField, location='query')
        def view(name):
            return {'name': name}
        self.api.add_view(view)

        response = self.client.get('/view?name=foo')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {'name': 'foo'})

    def test_body_location(self):
        class Schema(serialization.Schema):
            first_name = serialization.StringField()
            last_name = serialization.StringField()

        @route('/view', methods=['POST'])
        @param('user', Schema, location='body')
        def view(user):
            return user
        self.api.add_view(view)

        data = {'first_name': 'foo', 'last_name': 'bar'}

        response = self.client.post('/view', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), data)

    def test_invalid_location(self):
        @route('/view')
        @param('name', serialization.StringField, location='not_found')
        def view(name):
            pass
        self.api.add_view(view)

        response = self.client.get('/view?name=foo')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(json.loads(response.data),
                         {'errors': [{'message': 'Argument provider for location "not_found" not found.'}]})


class TestWithoutLocation(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.debug = True
        self.api = WebAPI(self.app)
        self.client = self.app.test_client()

    def test_query_param_without_location(self):
        @route('/view')
        @param('name', serialization.StringField())
        def view(name):
            return {'name': name}
        self.api.add_view(view)

        response = self.client.get('/view?name=foo')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {'name': 'foo'})

    def test_form_param_without_location(self):
        @route('/view', methods=['POST'])
        @param('name', serialization.StringField())
        def view(name):
            return {'name': name}
        self.api.add_view(view)

        response = self.client.post('/view', data={'name': 'foo'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {'name': 'foo'})

    def test_body_param_without_location(self):
        class Schema(serialization.Schema):
            first_name = serialization.StringField()
            last_name = serialization.StringField()

        @route('/view', methods=['POST'])
        @param('user', Schema)
        def view(user):
            return user
        self.api.add_view(view)

        data = {'first_name': 'foo', 'last_name': 'bar'}

        response = self.client.post('/view', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), data)


class TestInputError(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.debug = True
        self.api = WebAPI(self.app)
        self.client = self.app.test_client()

    def test_error_on_field(self):
        @route('/view')
        @param('name', serialization.StringField)
        def view(name):
            pass
        self.api.add_view(view)

        response = self.client.get('/view')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.data),
                         {'errors': [{'message': 'This field is required.', 'field': 'name'}]})

    def test_error_on_schema(self):
        class Schema(serialization.Schema):
            name = serialization.StringField()

        @route('/view')
        @param('user', Schema)
        def view(user):
            pass

        self.api.add_view(view)

        response = self.client.get('/view')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.data),
                         {'errors': [{'message': 'This field is required.', 'field': 'name'}]})

    def test_malformed_data(self):
        class Schema(serialization.Schema):
            name = serialization.StringField()

        @route('/view', methods=['POST'])
        @param('user', Schema, location='body')
        def view(user):
            pass

        self.api.add_view(view)

        response = self.client.post('/view', data='invalid data', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_unsupported_content_type(self):
        class Schema(serialization.Schema):
            name = serialization.StringField()

        @route('/view', methods=['POST'])
        @param('user', Schema, location='body')
        def view(user):
            pass
        self.api.add_view(view)

        data = {'name': 'foo'}

        response = self.client.post('/view', data=data, content_type='application/data')
        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(json.loads(response.data),
                         {'errors': [{'message': 'Unsupported media type "application/data" in request.'}]})
