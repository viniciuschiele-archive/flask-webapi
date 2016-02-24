from flask import Flask, json, Response
from flask_webapi import WebAPI, ControllerBase
from flask_webapi.decorators import route
from flask_webapi.decorators import error_handler
from flask_webapi.exceptions import APIException, AuthenticationFailed, MethodNotAllowed, UnsupportedMediaType, \
    ValidationError
from unittest import TestCase
from werkzeug.exceptions import BadRequest


class TestAPIException(TestCase):
    def test_default_message(self):
        self.assertEqual(APIException().message, APIException.default_message)

    def test_user_message(self):
        self.assertEqual(APIException('error message.').message, 'error message.')

    def test_str(self):
        self.assertEqual(str(APIException('error message.')), 'error message.')


class TestValidationError(TestCase):
    def test_string_message(self):
        self.assertEqual(ValidationError('error message').message, ['error message'])

    def test_list_message(self):
        message = ['error message 1', 'error message 2']
        self.assertEqual(ValidationError(message).message, message)

    def test_dict_message(self):
        message = dict(message='error message', code='error code')
        self.assertEqual(ValidationError(message).message, [message])

    def test_has_fields(self):
        message = {'user_id': {'message': 'error message', 'code': 'error code'}}
        self.assertEqual(ValidationError(message, has_fields=True).message, message)


class TestMethodNotAllowed(TestCase):
    def test_default_message(self):
        method = 'my_method'
        self.assertEqual(MethodNotAllowed(method).message, MethodNotAllowed.default_message.format(method=method))

    def test_user_message(self):
        method = 'my_method'
        self.assertEqual(MethodNotAllowed(method, 'error message').message, 'error message')


class TestUnsupportedMediaType(TestCase):
    def test_default_message(self):
        mimetype = 'application/json'
        self.assertEqual(UnsupportedMediaType(mimetype).message,
                         UnsupportedMediaType.default_message.format(mimetype=mimetype))

    def test_user_message(self):
        mimetype = 'application/json'
        self.assertEqual(UnsupportedMediaType(mimetype, 'error message').message, 'error message')


class TestController(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.api.add_controller(Controller)
        self.client = self.app.test_client()

    def test_api_exception(self):
        response = self.client.get('/api_exception')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response.get_data(as_text=True)),
                         dict(errors=[dict(message='Incorrect authentication credentials.')]))

    def test_user_exception(self):
        response = self.client.get('/user_exception')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(json.loads(response.get_data(as_text=True)),
                         dict(errors=[dict(message='A server error occurred.')]))

    def test_http_error(self):
        response = self.client.get('/http_exception')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.get_data(as_text=True)),
                         dict(errors=[dict(message=BadRequest.description)]))

    def test_validation_exception(self):
        response = self.client.get('/validation_exception')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.get_data(as_text=True)),
                         dict(errors=[dict(message='User not found.', field='user_id')]))

    def test_customer_error_handler(self):
        response = self.client.get('/custom_error_handler')
        self.assertEqual(response.status_code, 501)
        self.assertEqual('A server error occurred.', response.get_data(as_text=True))


def app_error_handler(error):
    return Response(str(error), status=501)


class Controller(ControllerBase):
    @route('/api_exception')
    def api_exception(self):
        raise AuthenticationFailed()

    @route('/user_exception')
    def user_exception(self):
        raise Exception()

    @route('/http_exception')
    def http_exception(self):
        raise BadRequest()

    @route('/validation_exception')
    def validation_exception(self):
        raise ValidationError(dict(message='User not found.', field='user_id'))

    @route('/custom_error_handler')
    @error_handler(app_error_handler)
    def custom_error_handler(self):
        raise APIException()
