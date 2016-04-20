from flask_webapi.utils import missing
from flask_webapi.utils.mimetypes import MimeType
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
