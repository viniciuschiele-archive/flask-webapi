from collections import OrderedDict
from flask import Flask, json
from flask_webapi import WebAPI, ViewBase, serializers
from flask_webapi.decorators import route, serializer
from unittest import TestCase


class TestSerializer(TestCase):
    def test_missing_data_during_deserialization(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.StringField()
            field_2 = serializers.StringField()

        serializer = Serializer()

        input = {'field_1': 'value_1'}
        output = serializer.load(input)

        self.assertEqual(input, output)

    def test_missing_attribute_during_serialization(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.StringField()
            field_2 = serializers.StringField()

        serializer = Serializer()

        input = {'field_1': 'value_1'}
        output = serializer.dump(input)

        self.assertEqual(input, output)

    def test_partial(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.StringField()
            field_2 = serializers.StringField(required=True)

        serializer = Serializer(partial=True)

        input = {'field_1': 'value_1'}
        output = serializer.load(input)

        self.assertEqual(input, output)

    def test_dump_with_errors(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.IntegerField()

        serializer = Serializer()

        data = {'field_1': 'value_1'}

        with self.assertRaises(ValueError):
            serializer.dump(data)

    def test_dump_without_errors(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.StringField()

        serializer = Serializer()

        input = {'field_1': 'value_1'}
        output = serializer.dump(input)

        self.assertEqual(output, input)

    def test_load_with_errors(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.IntegerField()

        serializer = Serializer()

        input = {'field_1': 'value_1'}
        output, errors = serializer.load(input)

        self.assertIsNone(output)
        self.assertEqual(errors, OrderedDict({'field_1': ['A valid integer is required.']}))


class TestView(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.api.add_view(View)
        self.client = self.app.test_client()

    def test_single_result(self):
        response = self.client.get('/single_result')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(field='value'))

    def test_multiple_results(self):
        response = self.client.get('/multiple_results')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), [dict(field='value')])

    def test_multiple_results_with_envelope(self):
        response = self.client.get('/multiple_results_with_envelope')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(results=[dict(field='value')]))

    def test_none_with_envelope(self):
        response = self.client.get('/none_with_envelope')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b'')


class Serializer(serializers.Serializer):
    field = serializers.StringField()


class View(ViewBase):
    @route('/single_result')
    @serializer(Serializer)
    def single_result(self):
        return {'field': 'value'}

    @route('/multiple_results')
    @serializer(Serializer, many=True)
    def multiple_results(self):
        return [{'field': 'value'}]

    @route('/multiple_results_with_envelope')
    @serializer(Serializer, many=True, envelope='results')
    def multiple_results_with_envelope(self):
        return [{'field': 'value'}]

    @route('/none_with_envelope')
    @serializer(Serializer, envelope='results')
    def none_with_envelope(self):
        return None
