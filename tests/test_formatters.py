import pickle

from flask import Flask, json, Response
from flask_webapi import WebAPI
from flask_webapi.formatters import OutputFormatter, JsonOutputFormatter, PickleOutputFormatter, MimeType
from flask_webapi.routers import route
from flask_webapi.utils import missing
from unittest import TestCase


class TestMimeType(TestCase):
    def test_parse_valid_mimetype(self):
        mimetype = MimeType.parse('application/json')

        self.assertEqual('application', mimetype.main_type)
        self.assertEqual('json', mimetype.sub_type)
        self.assertEqual({}, mimetype.params)

    def test_parse_empty_mimetype(self):
        mimetype = MimeType.parse('')

        self.assertEqual('', mimetype.main_type)
        self.assertEqual('', mimetype.sub_type)

    def test_parse_incomplete_mimetype(self):
        mimetype = MimeType.parse('application')

        self.assertEqual('application', mimetype.main_type)
        self.assertEqual('', mimetype.sub_type)

    def test_parse_mimetype_with_parameters(self):
        mimetype = MimeType.parse('application/json ; encoding = utf-8;indent=4')

        self.assertEqual('application', mimetype.main_type)
        self.assertEqual('json', mimetype.sub_type)
        self.assertEqual('utf-8', mimetype.params['encoding'])
        self.assertEqual('4', mimetype.params['indent'])

    def test_parse_mimetype_with_empty_parameter(self):
        mimetype = MimeType.parse('application/json;=utf-8;indent=')

        self.assertEqual(missing, mimetype.params.get('encoding', missing))
        self.assertEqual(missing, mimetype.params.get('indent', missing))

    def test_parse_mimetype_with_parameter_multiple_equals(self):
        mimetype = MimeType.parse('application/json;indent=1=2')

        self.assertEqual(missing, mimetype.params.get('indent', missing))

    def test_match_with_params(self):
        mimetype = MimeType.parse('application/json')
        mimetype2 = MimeType.parse('application/json;encoding=utf-8')
        self.assertTrue(mimetype.match(mimetype2))
        self.assertTrue(mimetype2.match(mimetype))

    def test_match_with_different_main_types(self):
        mimetype = MimeType.parse('application/json')
        mimetype2 = MimeType.parse('otherthing/json')
        self.assertFalse(mimetype.match(mimetype2))
        self.assertFalse(mimetype2.match(mimetype))

    def test_match_with_different_sub_types(self):
        mimetype = MimeType.parse('application/json')
        mimetype2 = MimeType.parse('application/xml')
        self.assertFalse(mimetype.match(mimetype2))
        self.assertFalse(mimetype2.match(mimetype))

    def test_match_with_star(self):
        mimetype = MimeType.parse('application/json')
        mimetype2 = MimeType.parse('application/*')
        self.assertTrue(mimetype.match(mimetype2))
        self.assertTrue(mimetype2.match(mimetype))

        mimetype = MimeType.parse('application/json')
        mimetype2 = MimeType.parse('*/json')
        self.assertTrue(mimetype.match(mimetype2))
        self.assertTrue(mimetype2.match(mimetype))


class TestView(TestCase):

    class OutputFormatterA(OutputFormatter):
        mimetype = MimeType.parse('application/formattera')

        def write(self, response, data, mimetype=None):
            response.set_data('FormatterA')
            response.content_type = str(mimetype)

    class OutputFormatterB(OutputFormatter):
        mimetype = MimeType.parse('application/formatterb')

        def write(self, response, data, mimetype=None):
            response.set_data('FormatterB')
            response.content_type = str(mimetype)

    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.api.output_formatters = []
        self.api.output_formatters.append(self.OutputFormatterA())
        self.api.output_formatters.append(self.OutputFormatterB())
        self.client = self.app.test_client()

        @route('/view')
        def view():
            return 'text'

        self.api.add_view(view)

    def test_formatter_with_accept_empty(self):
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/formattera')
        self.assertEqual(response.data.decode(), 'FormatterA')

    def test_formatter_with_accept_specified(self):
        response = self.client.get('/view', headers={'accept': 'application/formatterb'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/formatterb')
        self.assertEqual(response.data.decode(), 'FormatterB')

    def test_formatter_with_accept_any(self):
        response = self.client.get('/view', headers={'accept': '*/*'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/formattera')
        self.assertEqual(response.data.decode(), 'FormatterA')

    def test_formatter_with_accept_unsupported(self):
        response = self.client.get('/view', headers={'accept': 'application/renderer'})
        self.assertEqual(response.status_code, 406)


class TestJsonOutputFormatter(TestCase):
    def setUp(self):
        self.formatter = JsonOutputFormatter()

    def test_indent_present(self):
        self.assertEqual(self.formatter.get_indent(MimeType.parse('application/json;indent=10')), 10)

    def test_indent_not_present(self):
        self.assertEqual(self.formatter.get_indent(MimeType.parse('application/json')), None)

    def test_min_indent(self):
        self.assertEqual(self.formatter.get_indent(MimeType.parse('application/json;indent=-1')), None)

    def test_invalid_indent(self):
        self.assertEqual(self.formatter.get_indent(MimeType.parse('application/json;indent=a')), None)

    def test_write(self):
        data = dict(field='value')
        response = Response()

        self.formatter.write(response, data)
        self.assertEqual(response.get_data(), b'{"field": "value"}')
        self.assertEqual(json.loads(response.get_data()), data)


class TestPickleOutputFormatter(TestCase):
    def setUp(self):
        self.formatter = PickleOutputFormatter()

    def test_write(self):
        data = dict(field='value')
        response = Response()

        self.formatter.write(response, data)
        self.assertEqual(response.get_data(), b'\x80\x03}q\x00X\x05\x00\x00\x00fieldq\x01X\x05\x00\x00\x00valueq\x02s.')
        self.assertEqual(pickle.loads(response.get_data()), data)
