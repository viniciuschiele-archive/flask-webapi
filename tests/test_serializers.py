from collections import OrderedDict
from flask_webapi import serializers
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
