from collections import OrderedDict
from flask import Flask, json
from flask_webapi import WebAPI, serializers
from flask_webapi.decorators import route, serializer
from unittest import TestCase


class TestSerializer(TestCase):
    def test_missing_data_during_deserialization(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.StringField
            field_2 = serializers.StringField

        s = Serializer()

        input = {'field_1': 'value_1'}
        output = s.load(input)

        self.assertEqual(input, output)

    def test_missing_attribute_during_serialization(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.StringField
            field_2 = serializers.StringField

        s = Serializer()

        input = {'field_1': 'value_1'}
        output = s.dump(input)

        self.assertEqual(input, output)

    def test_partial(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.StringField
            field_2 = serializers.StringField(required=True)

        s = Serializer(partial=True)

        input = {'field_1': 'value_1'}
        output = s.load(input)

        self.assertEqual(input, output)

    def test_dump_with_errors(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.IntegerField

        s = Serializer()

        data = {'field_1': 'value_1'}

        with self.assertRaises(ValueError):
            s.dump(data)

    def test_dump_without_errors(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.StringField

        s = Serializer()

        input = {'field_1': 'value_1'}
        output = s.dump(input)

        self.assertEqual(output, input)

    def test_load_with_errors(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.IntegerField

        s = Serializer()

        input = {'field_1': 'value_1'}
        output, errors = s.load(input)

        self.assertIsNone(output)
        self.assertEqual(errors, OrderedDict({'field_1': ['A valid integer is required.']}))


class TestView(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.client = self.app.test_client()

    def test_single_result(self):
        class Serializer(serializers.Serializer):
            field = serializers.StringField

        @route('/view')
        @serializer(Serializer)
        def view():
            return {'field': 'value'}

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(field='value'))

    def test_multiple_results(self):
        class Serializer(serializers.Serializer):
            field = serializers.StringField

        @route('/view')
        @serializer(Serializer, many=True)
        def view():
            return [{'field': 'value'}]

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), [dict(field='value')])

    def test_multiple_results_with_envelope(self):
        class Serializer(serializers.Serializer):
            field = serializers.StringField

        @route('/view')
        @serializer(Serializer, many=True, envelope='results')
        def view():
            return [{'field': 'value'}]

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(results=[dict(field='value')]))

    def test_none_with_envelope(self):
        class Serializer(serializers.Serializer):
            field = serializers.StringField

        @route('/view')
        @serializer(Serializer, envelope='results')
        def view():
            return None

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b'')
