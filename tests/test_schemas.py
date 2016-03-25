import datetime
import uuid

# PyPy does no support Enum
try:
    from enum import Enum
except ImportError:
    Enum = None

from flask import Flask, json
from flask_webapi import WebAPI, exceptions, fields, schemas
from flask_webapi.decorators import route, serializer
from flask_webapi.exceptions import ValidationError
from unittest import TestCase


class TestNotImplemented(TestCase):
    def test_load(self):
        class Schema(schemas.Schema):
            field = fields.Field()

        with self.assertRaises(NotImplementedError):
            Schema().load({'field': 123})

    def test_dump(self):
        class Schema(schemas.Schema):
            field = fields.Field()

        with self.assertRaises(NotImplementedError):
            Schema().dump({'field': 123})


class TestAllowBlank(TestCase):
    def test_allow_blank(self):
        class Schema(schemas.Schema):
            field = fields.StringField(allow_blank=True)

        data = {'field': ''}
        self.assertEqual(Schema().load(data), data)

    def test_disallow_blank(self):
        class Schema(schemas.Schema):
            field = fields.StringField()

        with self.assertRaises(exceptions.ValidationError) as exc_info:
            data = {'field': ''}
            self.assertEqual(Schema().load(data), data)

        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('This field may not be blank.')]})

    def test_disallow_blank_and_allow_none(self):
        class Schema(schemas.Schema):
            field = fields.StringField(allow_none=True)

        data = {'field': ''}
        self.assertEqual(Schema().load(data), {'field': None})


class TestAllowNone(TestCase):
    def test_allow_none(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField(allow_none=True)

        data = {'field': None}
        self.assertEqual(Schema().load(data), data)

    def test_disallow_none(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField()

        with self.assertRaises(exceptions.ValidationError) as exc_info:
            data = {'field': None}
            self.assertEqual(Schema().load(data), data)

        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('This field may not be null.')]})


class TestDefault(TestCase):
    def test_default_on_loading(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField(default=123)

        data = {}
        self.assertEqual(Schema().load(data), {'field': 123})

    def test_callable_default_on_loading(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField(default=lambda: 123)

        data = {}
        self.assertEqual(Schema().load(data), {'field': 123})

    def test_bypass_default_on_loading(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField(default=123)

        data = {'field': 456}
        self.assertEqual(Schema().load(data), {'field': 456})

    def test_default_on_dumping(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField(default=123)

        data = {}
        self.assertEqual(Schema().dump(data), {'field': 123})

    def test_default_missing_on_dumping(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField()

        data = {}
        self.assertEqual(Schema().dump(data), {})


class TestRequired(TestCase):
    def test_required(self):
        class Schema(schemas.Schema):
            field = fields.StringField()

        data = {}
        with self.assertRaises(exceptions.ValidationError):
            Schema().load(data)

        data = {'field': 'value'}
        self.assertEqual(Schema().load(data), data)

    def test_non_required(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField(required=False)

        data = {}
        self.assertEqual(Schema().load(data), data)


class TestDumpTo(TestCase):
    def test_dump_to(self):
        class Schema(schemas.Schema):
            field = fields.StringField(dump_to='other')

        data = Schema().dump({'field': 'abc'})
        self.assertEqual(data, {'other': 'abc'})


class TestDumpOnly(TestCase):
    def test_load_with_dump_only(self):
        class Schema(schemas.Schema):
            field_1 = fields.IntegerField(dump_only=True)
            field_2 = fields.IntegerField()

        data = {'field_1': 123, 'field_2': 456}

        self.assertEqual(Schema().load(data), {'field_2': 456})

    def test_dump_with_dump_only(self):
        class Schema(schemas.Schema):
            field_1 = fields.IntegerField(dump_only=True)
            field_2 = fields.IntegerField()

        data = {'field_1': 123, 'field_2': 456}

        self.assertEqual(Schema().dump(data), data)


class TestLoadFrom(TestCase):
    def test_load_from(self):
        class Schema(schemas.Schema):
            field = fields.StringField(load_from='other')

        data = Schema().load({'other': 'abc'})
        self.assertEqual(data, {'field': 'abc'})


class TestLoadOnly(TestCase):
    def test_dump_with_load_only(self):
        class Schema(schemas.Schema):
            field_1 = fields.IntegerField(load_only=True)
            field_2 = fields.IntegerField()

        data = {'field_1': 123, 'field_2': 456}

        self.assertEqual(Schema().dump(data), {'field_2': 456})

    def test_load_with_load_only(self):
        class Schema(schemas.Schema):
            field_1 = fields.IntegerField(load_only=True)
            field_2 = fields.IntegerField()

        data = {'field_1': 123, 'field_2': 456}

        self.assertEqual(Schema().load(data), data)


class TestPartial(TestCase):
    def test_required(self):
        class Schema(schemas.Schema):
            field_1 = fields.IntegerField()
            field_2 = fields.IntegerField()

        s = Schema(partial=True)

        data = {'field_1': 123}

        self.assertEqual(s.load(data), data)

    def test_default(self):
        class Schema(schemas.Schema):
            field_1 = fields.IntegerField()
            field_2 = fields.IntegerField(default=456)

        s = Schema(partial=True)

        data = {'field_1': 123}

        self.assertEqual(s.load(data), data)


class TestOnly(TestCase):
    def test_only_as_string(self):
        class Schema(schemas.Schema):
            pass

        with self.assertRaises(AssertionError) as exc_info:
            Schema(only='field_1')
        self.assertEqual(str(exc_info.exception), '`only` has to be a list or tuple')

    def test_dump_with_only_fields(self):
        class Schema(schemas.Schema):
            field_1 = fields.IntegerField()
            field_2 = fields.IntegerField()

        data = {'field_1': 123, 'field_2': 456}
        expected = {'field_1': 123}

        s = Schema(only=['field_1'])
        self.assertEqual(s.dump(data), expected)

    def test_load_with_only_fields(self):
        class Schema(schemas.Schema):
            field_1 = fields.IntegerField()
            field_2 = fields.IntegerField()

        data = {'field_1': 123, 'field_2': 456}
        expected = {'field_2': 456}

        s = Schema(only=['field_2'])
        self.assertEqual(s.load(data), expected)


class TestErrorMessages(TestCase):
    def test_invalid_error_key(self):
        """
        If a field raises a validation error, but does not have a corresponding
        error message, then raise an appropriate assertion error.
        """

        class FailField(fields.Field):
            def _load(self, value):
                self._fail('incorrect')

        class Schema(schemas.Schema):
            field = FailField()

        with self.assertRaises(AssertionError) as exc_info:
            Schema().load({'field': 'value'})

        self.assertEqual(str(exc_info.exception),
                         'ValidationError raised by `FailField`, but error key '
                         '`incorrect` does not exist in the `error_messages` dictionary.')

    def test_dict_error_message(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField(error_messages={'invalid': {'message': 'error message', 'code': 123}})

        with self.assertRaises(ValidationError) as exc_info:
            Schema().load({'field': 'value'})

        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('error message', code=123)]})


class TestValidators(TestCase):
    def test_validator_without_return(self):
        def validate(value):
            pass

        class Schema(schemas.Schema):
            field = fields.IntegerField(validators=[validate])

        data = {'field': 123}

        self.assertEqual(Schema().load(data), data)

    def test_validator_returning_true(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField(validators=[lambda x: True])

        data = {'field': 123}

        self.assertEqual(Schema().load(data), data)

    def test_validator_returning_false(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField(validators=[lambda x: False])

        data = {'field': 123}

        with self.assertRaises(exceptions.ValidationError) as exc_info:
            Schema().load(data)
        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('Invalid value.')]})

    def test_validator_throwing_exception(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField(validators=[lambda x: 1 / 0])

        data = {'field': 123}

        with self.assertRaises(ZeroDivisionError) as exc_info:
            Schema().load(data)
        self.assertEqual(str(exc_info.exception), 'division by zero')

    def test_validator_throwing_validation_error(self):
        def validate(value):
            raise exceptions.ValidationError('Invalid value: ' + str(value))

        class Schema(schemas.Schema):
            field = fields.IntegerField(validators=[validate])

        data = {'field': 123}

        with self.assertRaises(exceptions.ValidationError) as exc_info:
            Schema().load(data)
        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('Invalid value: 123')]})

    def test_validator_on_serializer_throwing_validation_error(self):
        def validate(value):
            raise exceptions.ValidationError({'field': 'Invalid value: ' + str(value.get('field'))})

        class Schema(schemas.Schema):
            field = fields.IntegerField()

        data = {'field': 123}

        with self.assertRaises(exceptions.ValidationError) as exc_info:
            Schema(validators=[validate]).load(data)
        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('Invalid value: 123')]})

    def test_validator_on_serializer_throwing_validation_error_without_field_name(self):
        def validate(value):
            raise exceptions.ValidationError('Invalid value: ' + str(value.get('field')))

        class Schema(schemas.Schema):
            field = fields.IntegerField()

        data = {'field': 123}

        with self.assertRaises(exceptions.ValidationError) as exc_info:
            Schema(validators=[validate]).load(data)
        self.assertEqual(exc_info.exception.message, {'_serializer': [ValidationError('Invalid value: 123')]})

    def test_multi_validator_throwing_validation_error(self):
        def validate1(value):
            raise exceptions.ValidationError('Invalid value.')

        def validate2(value):
            raise exceptions.ValidationError('Invalid value 2.')

        class Schema(schemas.Schema):
            field = fields.IntegerField(validators=[validate1, validate2])

        data = {'field': 123}

        with self.assertRaises(exceptions.ValidationError) as exc_info:
            Schema().load(data)
        self.assertEqual(exc_info.exception.message,
                         {'field': [ValidationError('Invalid value.'), ValidationError('Invalid value 2.')]})

    def test_multi_validator_on_serializer_throwing_validation_error(self):
        def validate1(value):
            raise exceptions.ValidationError({'field': 'Invalid value.'})

        def validate2(value):
            raise exceptions.ValidationError({'field': 'Invalid value 2.'})

        class Schema(schemas.Schema):
            field = fields.IntegerField()

        data = {'field': 123}

        with self.assertRaises(exceptions.ValidationError) as exc_info:
            Schema(validators=[validate1, validate2]).load(data)
        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('Invalid value.')]})


class TestPost(TestCase):
    def test_post_dump(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField()

            def post_dump(self, data, original_data):
                data['field'] = 1
                return data

        self.assertEqual(Schema().dump({'field': 123}), {'field': 1})

    def test_post_dumps(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField()

            def post_dumps(self, data, original_data):
                return {'result': data}

        data = [{'field': 123}]
        result = {'result': [{'field': 123}]}

        self.assertEqual(Schema().dumps(data), result)

    def test_post_load(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField()

            def post_load(self, data, original_data):
                data['field'] = 1
                return data

        self.assertEqual(Schema().load({'field': 123}), {'field': 1})

    def test_post_loads(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField()

            def post_loads(self, data, original_data):
                data[0]['field'] = 1
                return data

        data = [{'field': 123}]
        result = [{'field': 1}]

        self.assertEqual(Schema().loads(data), result)

    def test_post_validate(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField()

            def post_validate(self, data):
                raise exceptions.ValidationError({'field': ['Invalid value']})

        with self.assertRaises(exceptions.ValidationError) as exc_info:
            Schema().load({'field': 1})
        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('Invalid value')]})


class TestDump(TestCase):
    def test_dump_with_dict(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField()

        data = {'field': 123}
        expected = {'field': 123}
        self.assertEqual(Schema().dump(data), expected)

    def test_dump_with_error(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField()

        data = {'field': 'value'}

        with self.assertRaises(ValueError):
            Schema().dump(data)

    def test_dump_with_model(self):
        class Model(object):
            field = 123

        class Schema(schemas.Schema):
            field = fields.IntegerField()

        output = Schema().dump(Model())

        self.assertEqual(output, {'field': 123})

    def test_dumps(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField()

        data = [{'field': 123}]
        expected = [{'field': 123}]
        self.assertEqual(Schema().dumps(data), expected)


class TestLoad(TestCase):
    def test_load_with_dict(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField()

        data = {'field': 123}
        expected = {'field': 123}
        self.assertEqual(Schema().load(data), expected)

    def test_load_with_error(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField()

        data = {'field': 'value'}

        with self.assertRaises(exceptions.ValidationError) as exc_info:
            Schema().load(data)
        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('A valid integer is required.')]})

    def test_load_with_model(self):
        class Model(object):
            field = 123

        class Schema(schemas.Schema):
            field = fields.IntegerField()

        with self.assertRaises(exceptions.ValidationError) as exc_info:
            Schema().load(Model())
        self.assertEqual(exc_info.exception.message, 'Invalid data. Expected a dictionary, but got Model.')

    def test_loads(self):
        class Schema(schemas.Schema):
            field = fields.IntegerField()

        data = [{'field': 123}]
        expected = [{'field': 123}]
        self.assertEqual(Schema().loads(data), expected)


class TestView(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.client = self.app.test_client()

    def test_single_result_with_many_none(self):
        class Schema(schemas.Schema):
            field = fields.StringField()

        @route('/view')
        @serializer(Schema)
        def view():
            return {'field': 'value'}

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(field='value'))

    def test_single_result_with_many_false(self):
        class Schema(schemas.Schema):
            field = fields.StringField()

        @route('/view')
        @serializer(Schema, many=False)
        def view():
            return {'field': 'value'}

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(field='value'))

    def test_multiple_results_with_many_none(self):
        class Schema(schemas.Schema):
            field = fields.StringField()

        @route('/view')
        @serializer(Schema)
        def view():
            return [{'field': 'value'}]

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), [dict(field='value')])

    def test_multiple_results_with_many_true(self):
        class Schema(schemas.Schema):
            field = fields.StringField()

        @route('/view')
        @serializer(Schema, many=True)
        def view():
            return [{'field': 'value'}]

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), [dict(field='value')])

    def test_multiple_results_with_envelope(self):
        class Schema(schemas.Schema):
            field = fields.StringField()

        @route('/view')
        @serializer(Schema, many=True, envelope='results')
        def view():
            return [{'field': 'value'}]

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(results=[dict(field='value')]))

    def test_none_with_envelope(self):
        class Schema(schemas.Schema):
            field = fields.StringField()

        @route('/view')
        @serializer(Schema, envelope='results')
        def view():
            return None

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b'')
