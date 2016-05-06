# from flask import Flask, request
# from flask_webapi.formatters import JsonInputFormatter, JsonOutputFormatter, PickleOutputFormatter, MimeType
# from flask_webapi.negotiators import DefaultContentNegotiator
# from unittest import TestCase

#
# class TestSelectInputFormatter(TestCase):
#     def setUp(self):
#         self.app = Flask(__name__)
#         self.negotiation = DefaultContentNegotiator()
#
#     def test_empty_formatters(self):
#         with self.app.test_request_context():
#             self.assertIsNone(self.negotiation.select_input_formatter([]))
#
#     def test_empty_content_type(self):
#         with self.app.test_request_context():
#             formatters = [JsonInputFormatter()]
#             self.assertIsNone(self.negotiation.select_input_formatter(formatters))
#
#     def test_valid_content_type(self):
#         with self.app.test_request_context(content_type='application/json;charset=utf-8'):
#             parsers = [JsonInputFormatter()]
#             parser, mimetype = self.negotiation.select_input_formatter(parsers)
#             self.assertEqual(parser, parsers[0])
#             self.assertEqual(mimetype, MimeType.parse(request.content_type))
#
#     def test_invalid_content_type(self):
#         with self.app.test_request_context(content_type='application/data'):
#             formatters = [JsonInputFormatter()]
#             self.assertIsNone(self.negotiation.select_input_formatter(formatters))
#
#
# class TestSelectOutputFormatter(TestCase):
#     def setUp(self):
#         self.app = Flask(__name__)
#         self.negotiation = DefaultContentNegotiator()
#
#     def test_empty_formatters(self):
#         with self.app.test_request_context():
#             self.assertIsNone(self.negotiation.select_output_formatter([]))
#
#     def test_empty_accept_header(self):
#         with self.app.test_request_context():
#             renderers = [JsonOutputFormatter(), PickleOutputFormatter()]
#             renderer, mimetype = self.negotiation.select_output_formatter(renderers)
#             self.assertEqual(renderer, renderers[0])
#             self.assertEqual(mimetype, renderers[0].mimetype)
#
#     def test_valid_accept_header(self):
#         with self.app.test_request_context(headers={'accept': 'application/json; indent=6'}):
#             renderers = [JsonOutputFormatter()]
#             renderer, mimetype = self.negotiation.select_output_formatter(renderers)
#             self.assertEqual(renderer, renderers[0])
#             self.assertEqual(mimetype, MimeType.parse(request.headers['accept']))
#
#     def test_invalid_accept_header(self):
#         with self.app.test_request_context(headers={'accept': 'application/data'}):
#             formatters = [JsonOutputFormatter()]
#             self.assertIsNone(self.negotiation.select_output_formatter(formatters))
#
#     def test_multiple_accept_header(self):
#         with self.app.test_request_context(headers={'accept': 'application/xml,application/json;'}):
#             renderers = [JsonOutputFormatter()]
#             renderer, mimetype = self.negotiation.select_output_formatter(renderers)
#             self.assertEqual(renderer, renderers[0])
#             self.assertEqual(str(mimetype), 'application/json')
#
#     def test_any_in_accept_header(self):
#         with self.app.test_request_context(headers={'accept': '*/*'}):
#             renderers = [JsonOutputFormatter()]
#             renderer, mimetype = self.negotiation.select_output_formatter(renderers)
#             self.assertEqual(renderer, renderers[0])
#             self.assertEqual(str(mimetype), 'application/json')
