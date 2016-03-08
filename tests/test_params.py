# from flask import Flask, json
# from flask_webapi import WebAPI, serializers
# from flask_webapi.decorators import param, route
# from werkzeug.datastructures import Headers
# from unittest import TestCase
#
#
# class TestQueryString(TestCase):
#     def setUp(self):
#         self.app = Flask(__name__)
#         self.api = WebAPI(self.app)
#         self.client = self.app.test_client()
#
#     def test_empty_param(self):
#         @route('/view')
#         @param('param_1', serializers.StringField, location='query')
#         def view(param_1):
#             return {'param_1': param_1}
#         self.api.add_view(view)
#         response = self.client.get('/view?param_1=')
#         self.assertEqual(response.status_code, 400)
#         self.assertEqual(json.loads(response.data),
#                          dict(errors=[dict(message='This field may not be null.', field='param_1')]))
#
#     def test_missing_param(self):
#         @route('/view')
#         @param('param_1', serializers.StringField, location='query')
#         def view(param_1):
#             return {'param_1': param_1}
#         self.api.add_view(view)
#         response = self.client.get('/view')
#         self.assertEqual(response.status_code, 500)
#         self.assertEqual(json.loads(response.data),
#                          dict(errors=[dict(message='A server error occurred.')]))
#
#     def test_valid_param(self):
#         @route('/view')
#         @param('param_1', serializers.StringField, location='query')
#         def view(param_1):
#             return {'param_1': param_1}
#         self.api.add_view(view)
#         response = self.client.get('/view?param_1=value')
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(json.loads(response.data), dict(param_1='value'))
#
#     def test_invalid_param(self):
#         @route('/view')
#         @param('param_1', serializers.IntegerField, location='query')
#         def view(param_1):
#             pass
#         self.api.add_view(view)
#         response = self.client.get('/view?param_1=a')
#         self.assertEqual(response.status_code, 400)
#         self.assertEqual(json.loads(response.data),
#                          dict(errors=[dict(message='A valid integer is required.', field='param_1')]))
#
#     def test_list_param(self):
#         @route('/view')
#         @param('param_1', serializers.ListField(serializers.IntegerField), location='query')
#         def view(param_1):
#             return {'param_1': param_1}
#         self.api.add_view(view)
#         response = self.client.get('/view?param_1=1&param_1=2')
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(json.loads(response.data), dict(param_1=[1, 2]))
#
#     def test_missing_list_param(self):
#         @route('/view')
#         @param('param_1', serializers.ListField(serializers.IntegerField), location='query')
#         def view(param_1):
#             return {'param_1': param_1}
#
#         self.api.add_view(view)
#         response = self.client.get('/view')
#         self.assertEqual(response.status_code, 500)
#         self.assertEqual(json.loads(response.data),
#                          dict(errors=[dict(message='A server error occurred.')]))
#
#     def test_multiple_params_with_serializer(self):
#         class Serializer(serializers.Serializer):
#             param_1 = serializers.StringField
#             param_2 = serializers.IntegerField
#
#         @route('/view')
#         @param('params', Serializer(), location='query')
#         def view(params):
#             return {'param_1': params['param_1'], 'param_2': params['param_2']}
#
#         self.api.add_view(view)
#         response = self.client.get('/view?param_1=a&param_2=1')
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(json.loads(response.data), dict(param_1='a', param_2=1))
#
#     def test_kwargs(self):
#         @route('/view')
#         @param('param_1', serializers.StringField, location='query')
#         def view(**kwargs):
#             return {'param_1': kwargs['param_1']}
#         self.api.add_view(view)
#         response = self.client.get('/view?param_1=value')
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(json.loads(response.data), dict(param_1='value'))
#
#
# class TestHeader(TestCase):
#     def setUp(self):
#         self.app = Flask(__name__)
#         self.api = WebAPI(self.app)
#         self.client = self.app.test_client()
#
#     def test_empty_param(self):
#         @route('/view')
#         @param('param_1', serializers.StringField, location='header')
#         def view(param_1):
#             return {'param_1': param_1}
#         self.api.add_view(view)
#
#         headers = Headers()
#         headers.add('param_1', '')
#         response = self.client.get('/view', headers=headers)
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(json.loads(response.data), dict(param_1=None))
#
#     def test_missing_param(self):
#         @route('/view')
#         @param('param_1', serializers.StringField, location='query')
#         def view(param_1):
#             return {'param_1': param_1}
#         self.api.add_view(view)
#         response = self.client.get('/view')
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(json.loads(response.data), dict(param_1=None))
#
#     def test_valid_param(self):
#         @route('/view')
#         @param('param_1', serializers.StringField, location='query')
#         def view(param_1):
#             return {'param_1': param_1}
#         self.api.add_view(view)
#         response = self.client.get('/view?param_1=value')
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(json.loads(response.data), dict(param_1='value'))
#
#     def test_invalid_param(self):
#         @route('/view')
#         @param('param_1', serializers.IntegerField, location='query')
#         def view(param_1):
#             pass
#         self.api.add_view(view)
#         response = self.client.get('/view?param_1=a')
#         self.assertEqual(response.status_code, 400)
#         self.assertEqual(json.loads(response.data),
#                          dict(errors=[dict(message='A valid integer is required.', field='param_1')]))
#
#     def test_list_param(self):
#         @route('/view')
#         @param('param_1', serializers.ListField(serializers.IntegerField), location='query')
#         def view(param_1):
#             return {'param_1': param_1}
#         self.api.add_view(view)
#         response = self.client.get('/view?param_1=1&param_1=2')
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(json.loads(response.data), dict(param_1=[1, 2]))
#
#     def test_empty_list_param(self):
#         @route('/view')
#         @param('param_1', serializers.ListField(serializers.IntegerField), location='query')
#         def view(param_1):
#             return {'param_1': param_1}
#
#         self.api.add_view(view)
#         response = self.client.get('/view')
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(json.loads(response.data), dict(param_1=None))
#
#     def test_multiple_params_with_serializer(self):
#         class Serializer(serializers.Serializer):
#             param_1 = serializers.StringField
#             param_2 = serializers.IntegerField
#
#         @route('/view')
#         @param('params', Serializer(), location='query')
#         def view(params):
#             return {'param_1': params['param_1'], 'param_2': params['param_2']}
#
#         self.api.add_view(view)
#         response = self.client.get('/view?param_1=a&param_2=1')
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(json.loads(response.data), dict(param_1='a', param_2=1))
#
#     def test_kwargs(self):
#         @route('/view')
#         @param('param_1', serializers.StringField, location='query')
#         def view(**kwargs):
#             return {'param_1': kwargs['param_1']}
#         self.api.add_view(view)
#         response = self.client.get('/view?param_1=value')
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(json.loads(response.data), dict(param_1='value'))
