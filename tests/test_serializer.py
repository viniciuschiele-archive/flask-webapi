from flask import Flask
from flask_webapi import WebAPI, APIView, Schema, fields, json, route, serializer
from unittest import TestCase


class TestSerializer(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.api.load_module('tests.test_serializer')
        self.client = self.app.test_client()

    def test_get_model(self):
        response = self.client.get('/models/1234')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.get_data(as_text=True)), dict(id='1234', name='model1'))

    def test_get_models(self):
        response = self.client.get('/models')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.get_data(as_text=True)), [dict(id='1234', name='model1')])

    def test_get_models_with_custom_fields(self):
        response = self.client.get('/models?fields=id')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.get_data(as_text=True)), [dict(id='1234')])

    def test_get_models_with_envelope(self):
        response = self.client.get('/models2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.get_data(as_text=True)), dict(models=[dict(id='1234', name='model1')]))

    def test_get_models_none_with_envelope(self):
        response = self.client.get('/models3')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.get_data(as_text=True)), dict(models=None))


class Model(object):
    id = None
    name = None


class ModelSchema(Schema):
    id = fields.String()
    name = fields.String()


class BasicView(APIView):
    @route('/models/<id>', methods=['GET'])
    @serializer(ModelSchema)
    def get_model(self, id):
        model = Model()
        model.id = id
        model.name = 'model1'
        return model

    @route('/models', methods=['GET'])
    @serializer(ModelSchema)
    def get_models(self):
        model = Model()
        model.id = '1234'
        model.name = 'model1'
        return [model]

    @route('/models2', methods=['GET'])
    @serializer(ModelSchema, envelope='models')
    def get_models_with_envelope(self):
        model = Model()
        model.id = '1234'
        model.name = 'model1'
        return [model]

    @route('/models3', methods=['GET'])
    @serializer(ModelSchema, envelope='models')
    def get_models_none_with_envelope(self):
        return None
