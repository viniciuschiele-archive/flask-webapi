from flask import Flask, request
from flask_webapi import WebAPI
from flask_webapi.authentication import authenticator, BaseAuthenticator
from flask_webapi.exceptions import AuthenticationFailed
from flask_webapi.views import route
from unittest import TestCase


class TestView(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.client = self.app.test_client()

    def test_valid_credentials(self):
        @route('/view')
        @authenticator(Authenticator)
        def view():
            self.assertEqual(request.user, 'user1')
            self.assertEqual(request.auth, '1234')

        self.api.add_view(view)
        response = self.client.get('/view', headers={'Authorization': '1234'})
        self.assertEqual(response.status_code, 204)

    def test_invalid_credentials(self):
        @route('/view')
        @authenticator(Authenticator)
        def view():
            self.assertEqual(request.user, None)
            self.assertEqual(request.auth, None)

        self.api.add_view(view)
        response = self.client.get('/view', headers={'Authorization': '9999'})
        self.assertEqual(response.status_code, 401)

    def test_missing_credentials(self):
        @route('/view')
        @authenticator(Authenticator)
        def view():
            self.assertEqual(request.user, None)
            self.assertEqual(request.auth, None)

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 204)


class Authenticator(BaseAuthenticator):
    def authenticate(self):
        auth = request.headers.get('Authorization')

        if not auth:
            return None

        if auth != '1234':
            raise AuthenticationFailed()

        return 'user1', auth
