from flask import Flask, request, Response
from flask_webapi import WebAPI, ViewBase
from flask_webapi.decorators import route, authenticator
from flask_webapi.exceptions import AuthenticationFailed
from flask_webapi.authentication import AuthenticatorBase
from unittest import TestCase


class TestAuthentication(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.api.add_view(View)
        self.client = self.app.test_client()

    def test_valid_credentials(self):
        response = self.client.post('/add', headers={'Authorization': '1234'})
        self.assertEqual(response.status_code, 200)

    def test_invalid_credentials(self):
        response = self.client.post('/add', headers={'Authorization': '9999'})
        self.assertEqual(response.status_code, 401)

    def test_without_credentials(self):
        response = self.client.post('/add')
        self.assertEqual(response.status_code, 500)


class BasicAuthenticator(AuthenticatorBase):
    def authenticate(self):
        auth = request.headers.get('Authorization')

        if not auth:
            return None

        if auth != '1234':
            raise AuthenticationFailed()

        return 'user1', auth


class View(ViewBase):
    @route('/add', methods=['POST'])
    @authenticator(BasicAuthenticator)
    def add(self):
        if request.user is None:
            raise Exception('user is not authenticated')

        return Response()
