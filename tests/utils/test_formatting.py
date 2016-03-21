from flask_webapi.utils.formatting import format_error_message
from unittest import TestCase


class TestFormatErrorMessage(TestCase):
    def test_string_message(self):
        input_message = 'Invalid value: {value}'
        expected_message = 'Invalid value: 123'

        self.assertEqual(format_error_message(input_message, value=123), expected_message)

    def test_dict_message(self):
        input_message = {'message': 'Invalid value: {value}'}
        expected_message = {'message': 'Invalid value: 123'}

        self.assertEqual(format_error_message(input_message, value=123), expected_message)
