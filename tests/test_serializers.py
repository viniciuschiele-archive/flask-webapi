from flask_webapi import serializers
from unittest import TestCase


class TestSerializer(TestCase):
    def test_missing_data_during_deserialization(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.StringField()
            field_2 = serializers.StringField()

        field = Serializer()

        input = {'field_1': 'value_1'}
        output = field.load(input)

        self.assertEqual(input, output)

    def test_missing_attribute_during_serialization(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.StringField()
            field_2 = serializers.StringField()

        field = Serializer()

        input = {'field_1': 'value_1'}
        output = field.dump(input)

        self.assertEqual(input, output)

    def test_partial(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.StringField()
            field_2 = serializers.StringField(required=True)

        field = Serializer(partial=True)

        input = {'field_1': 'value_1'}
        output = field.load(input)

        self.assertEqual(input, output)
