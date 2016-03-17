from flask import Flask
from flask_webapi import WebAPI
from flask_webapi.decorators import route, authenticator, permission
from flask_webapi.authentication import AuthenticatorBase
from flask_webapi.permissions import PermissionBase, IsAuthenticated
from unittest import TestCase


class TestView(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.client = self.app.test_client()

    def test_permission_granted(self):
        @route('/view')
        @authenticator(Authenticator)
        @permission(IsAuthenticated)
        def view():
            pass

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 204)

    def test_permission_denied(self):
        class Denied(PermissionBase):
            def has_permission(self):
                return False

        @route('/view')
        @authenticator(Authenticator)
        @permission(Denied)
        def view():
            pass

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated(self):
        @route('/view')
        @permission(IsAuthenticated)
        def view():
            pass

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 401)


class Authenticator(AuthenticatorBase):
    def authenticate(self):
        return 'user1', '1234'
