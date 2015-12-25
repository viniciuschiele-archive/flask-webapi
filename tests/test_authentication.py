from flask import Flask, request, Response
from flask_webapi import errors, WebAPI, APIView, route, authenticators
from flask_webapi.authentication import BaseAuthenticator
from unittest import TestCase


class TestAuthentication(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.api.load_module('tests.test_authentication')
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


class BasicAuthenticator(BaseAuthenticator):
    def authenticate(self):
        auth = request.headers.get('Authorization')

        if not auth:
            return None

        if auth != '1234':
            raise errors.AuthenticationFailed()

        return 'user1', auth


class BasicView(APIView):
    @route('/add', methods=['POST'])
    @authenticators(BasicAuthenticator)
    def add(self):
        if request.user is None:
            raise Exception('user is not authenticated')

        return Response()
