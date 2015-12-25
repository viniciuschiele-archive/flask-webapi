from flask import Flask, Response
from flask_webapi import WebAPI, APIView, route, authenticator, permissions
from flask_webapi.authentication import BaseAuthenticator
from flask_webapi.authorization import BasePermission, IsAuthenticated
from unittest import TestCase


class TestAuthorization(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.api.load_module('tests.test_authorization')
        self.client = self.app.test_client()

    def test_permission_granted(self):
        response = self.client.post('/add')
        self.assertEqual(response.status_code, 200)

    def test_permission_denied_without_credentials(self):
        response = self.client.post('/remove')
        self.assertEqual(response.status_code, 401)

    def test_permission_denied_with_credentials(self):
        response = self.client.post('/update')
        self.assertEqual(response.status_code, 403)


class AlwaysAuthenticated(BaseAuthenticator):
    def authenticate(self):
        return 'user1', '1234'


class NeverAuthenticated(BaseAuthenticator):
    def authenticate(self):
        return None


class NeverAllow(BasePermission):
    def has_permission(self):
        return False


class BasicView(APIView):
    @route('/add', methods=['POST'])
    @authenticator(AlwaysAuthenticated)
    @permissions(IsAuthenticated)
    def add(self):
        return Response()

    @route('/remove', methods=['POST'])
    @authenticator(NeverAuthenticated)
    @permissions(IsAuthenticated)
    def remove(self):
        return Response()

    @route('/update', methods=['POST'])
    @authenticator(AlwaysAuthenticated)
    @permissions(NeverAllow)
    def update(self):
        return Response()