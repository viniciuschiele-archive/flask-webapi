from flask import Flask, json, Response
from flask_webapi import WebAPI
from flask_webapi.decorators import route
from flask_webapi.exceptions import APIException, UnsupportedMediaType, ValidationError
from unittest import TestCase
from werkzeug.exceptions import BadRequest


class TestAPIException(TestCase):
    def test_default_message(self):
        self.assertEqual(APIException().message, APIException.default_message)

    def test_user_message(self):
        self.assertEqual(APIException('error message.').message, 'error message.')

    def test_str(self):
        self.assertEqual(str(APIException('error message.')), 'error message.')

    def test_eq(self):
        self.assertEqual(APIException('error message.'), APIException('error message.'))

    def test_ne(self):
        self.assertNotEqual(APIException('error message.'), APIException('error message 2.'))


class TestValidationError(TestCase):
    def test_string_message(self):
        error = ValidationError('error message')
        self.assertEqual(error.message, 'error message')

    def test_list_message_with_one_item(self):
        input_message = ['error message']
        error = ValidationError(input_message)
        self.assertEqual(error.message, 'error message')

    def test_list_message_with_dict(self):
        input_message = [{'message': 'error message', 'code': 123}]
        error = ValidationError(input_message)
        self.assertEqual(error.message, 'error message')
        self.assertEqual(error.kwargs, {'code': 123})

    def test_list_message_with_multi_items(self):
        input_message = ['error message 1', 'error message 2']
        expected_message = [ValidationError('error message 1'), ValidationError('error message 2')]
        error = ValidationError(input_message)
        self.assertEqual(error.message, expected_message)

    def test_dict_with_str(self):
        input_message = {'user_id': 'error message'}
        expected_message = {'user_id': [ValidationError('error message')]}
        error = ValidationError(input_message)
        self.assertEqual(error.message, expected_message)

    def test_dict_with_list(self):
        input_message = {'user_id': [{'message': 'error message', 'code': 'error code'}]}
        expected_message = {'user_id': [ValidationError('error message', code='error code')]}
        error = ValidationError(input_message)
        self.assertEqual(error.message, expected_message)


class TestUnsupportedMediaType(TestCase):
    def test_default_message(self):
        mimetype = 'application/json'
        self.assertEqual(UnsupportedMediaType(mimetype).message,
                         UnsupportedMediaType.default_message.format(mimetype=mimetype))

    def test_user_message(self):
        mimetype = 'application/json'
        self.assertEqual(UnsupportedMediaType(mimetype, 'error message').message, 'error message')


class TestDenormalize(TestCase):
    def test_string_message(self):
        errors = APIException('Invalid value.', field='name').denormalize()
        expected_errors = [{'message': 'Invalid value.', 'field': 'name'}]

        self.assertEqual(errors, expected_errors)

    def test_list_message(self):
        errors = ValidationError(['Invalid value.', 'Min size.']).denormalize()
        expected_errors = [{'message': 'Invalid value.'}, {'message': 'Min size.'}]

        self.assertEqual(errors, expected_errors)

    def test_dict_message(self):
        message = ValidationError({'name': ['Invalid value.', 'Min size.']})
        errors = message.denormalize()
        expected_errors = [
            {'message': 'Invalid value.', 'field': 'name'},
            {'message': 'Min size.', 'field': 'name'}
        ]

        self.assertEqual(errors, expected_errors)

    def test_dict_message_with_sub_dict(self):
        message = ValidationError({'company': {'name': ['Invalid value.', 'Min size.']}})
        errors = message.denormalize()
        expected_errors = [
            {'message': 'Invalid value.', 'field': 'company.name'},
            {'message': 'Min size.', 'field': 'company.name'}
        ]

        self.assertEqual(errors, expected_errors)


class TestView(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.client = self.app.test_client()

    def test_api_exception(self):
        @route('/view')
        def view():
            raise APIException('user error.')
        self.api.add_view(view)

        response = self.client.get('/view')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(json.loads(response.data), {'errors': [{'message': 'user error.'}]})

    def test_validation_exception(self):
        @route('/view')
        def view():
            raise ValidationError('User not found.', field='user_id')
        self.api.add_view(view)

        response = self.client.get('/view')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.data), {'errors': [{'message': 'User not found.', 'field': 'user_id'}]})

    def test_http_exception(self):
        @route('/view')
        def http_exception():
            raise BadRequest()
        self.api.add_view(http_exception)

        response = self.client.get('/view')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.data), {'errors': [{'message': BadRequest.description}]})

    def test_unhandled_exception(self):
        @route('/view')
        def view():
            raise Exception()
        self.api.add_view(view)

        response = self.client.get('/view')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(json.loads(response.data), {'errors': [{'message': 'A server error occurred.'}]})

    def test_exception_handler(self):
        def custom_exception_handler(view, e):
            return Response(e.message, status=400)

        @route('/view')
        def view():
            raise ValidationError('user error.')

        self.api.exception_handler = custom_exception_handler
        self.api.add_view(view)

        response = self.client.get('/view')
        self.assertEqual(response.status_code, 400)
        self.assertEqual('user error.', response.get_data(as_text=True))
