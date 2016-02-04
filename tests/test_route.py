from flask import Flask
from flask_webapi import WebAPI, ViewBase, route
from unittest import TestCase


class TestRoute(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.api.add_view(View)
        self.api.add_view(View2)
        self.api.add_view(view3)
        self.client = self.app.test_client()

    def test_204_response(self):
        response = self.client.post('/view/action')
        self.assertEqual(response.status_code, 204)

        response = self.client.post('/view2/action')
        self.assertEqual(response.status_code, 204)

        response = self.client.post('/view3/action')
        self.assertEqual(response.status_code, 204)

    def test_404_response(self):
        response = self.client.post('/view/action_not_found')
        self.assertEqual(response.status_code, 404)

        response = self.client.post('/view2/action_not_found')
        self.assertEqual(response.status_code, 404)

        response = self.client.post('/view3/action_not_found')
        self.assertEqual(response.status_code, 404)

    def test_405_response(self):
        response = self.client.put('/view/action')
        self.assertEqual(response.status_code, 405)

        response = self.client.put('/view2/action')
        self.assertEqual(response.status_code, 405)

        response = self.client.put('/view3/action')
        self.assertEqual(response.status_code, 405)


class View(ViewBase):
    @route('/view/action', methods=['POST'])
    def get(self):
        pass


@route('/view2')
class View2(ViewBase):
    @route('/action', methods=['POST'])
    def get(self):
        pass


@route('/view3/action', methods=['POST'])
def view3():
    pass
