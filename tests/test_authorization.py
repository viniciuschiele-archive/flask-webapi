from flask import Flask
from flask_webapi import WebAPI, authenticate, authorize, route
from flask_webapi.authenticators import Authenticator, AuthenticateResult
from flask_webapi.permissions import Permission, IsAuthenticated
from unittest import TestCase


class TestView(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.client = self.app.test_client()

    def test_permission_granted(self):
        @route('/view')
        @authenticate(FakeAuthenticator)
        @authorize(IsAuthenticated)
        def view():
            pass

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 204)

    def test_permission_denied(self):
        class Denied(Permission):
            def has_permission(self):
                return False

        @route('/view')
        @authenticate(FakeAuthenticator)
        @authorize(Denied)
        def view():
            pass

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated(self):
        @route('/view')
        @authorize(IsAuthenticated)
        def view():
            pass

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 401)


class FakeAuthenticator(Authenticator):
    def authenticate(self):
        return AuthenticateResult.success('user1', '1234')
