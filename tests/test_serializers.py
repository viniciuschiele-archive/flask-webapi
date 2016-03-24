import datetime
import uuid

# PyPy does no support Enum
try:
    from enum import Enum
except ImportError:
    Enum = None

from decimal import Decimal
from flask import Flask, json
from flask_webapi import WebAPI, serializers
from flask_webapi.decorators import route, serializer
from flask_webapi.exceptions import ValidationError
from flask_webapi.utils import timezone
from unittest import TestCase
from werkzeug.datastructures import MultiDict


class TestNotImplemented(TestCase):
    def test_load(self):
        class Serializer(serializers.Serializer):
            field = serializers.Field()

        with self.assertRaises(NotImplementedError):
            Serializer().load({'field': 123})

    def test_dump(self):
        class Serializer(serializers.Serializer):
            field = serializers.Field()

        with self.assertRaises(NotImplementedError):
            Serializer().dump({'field': 123})


class TestAllowBlank(TestCase):
    def test_allow_blank(self):
        class Serializer(serializers.Serializer):
            field = serializers.StringField(allow_blank=True)

        data = {'field': ''}
        self.assertEqual(Serializer().load(data), data)

    def test_disallow_blank(self):
        class Serializer(serializers.Serializer):
            field = serializers.StringField()

        with self.assertRaises(serializers.ValidationError) as exc_info:
            data = {'field': ''}
            self.assertEqual(Serializer().load(data), data)

        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('This field may not be blank.')]})

    def test_disallow_blank_and_allow_none(self):
        class Serializer(serializers.Serializer):
            field = serializers.StringField(allow_none=True)

        data = {'field': ''}
        self.assertEqual(Serializer().load(data), {'field': None})


class TestAllowNone(TestCase):
    def test_allow_none(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField(allow_none=True)

        data = {'field': None}
        self.assertEqual(Serializer().load(data), data)

    def test_disallow_none(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField()

        with self.assertRaises(serializers.ValidationError) as exc_info:
            data = {'field': None}
            self.assertEqual(Serializer().load(data), data)

        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('This field may not be null.')]})


class TestDefault(TestCase):
    def test_default_on_loading(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField(default=123)

        data = {}
        self.assertEqual(Serializer().load(data), {'field': 123})

    def test_callable_default_on_loading(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField(default=lambda: 123)

        data = {}
        self.assertEqual(Serializer().load(data), {'field': 123})

    def test_bypass_default_on_loading(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField(default=123)

        data = {'field': 456}
        self.assertEqual(Serializer().load(data), {'field': 456})

    def test_default_on_dumping(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField(default=123)

        data = {}
        self.assertEqual(Serializer().dump(data), {'field': 123})

    def test_default_missing_on_dumping(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField()

        data = {}
        self.assertEqual(Serializer().dump(data), {})


class TestRequired(TestCase):
    def test_required(self):
        class Serializer(serializers.Serializer):
            field = serializers.StringField()

        data = {}
        with self.assertRaises(serializers.ValidationError):
            Serializer().load(data)

        data = {'field': 'value'}
        self.assertEqual(Serializer().load(data), data)

    def test_non_required(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField(required=False)

        data = {}
        self.assertEqual(Serializer().load(data), data)


class TestDumpTo(TestCase):
    def test_dump_to(self):
        class Serializer(serializers.Serializer):
            field = serializers.StringField(dump_to='other')

        data = Serializer().dump({'field': 'abc'})
        self.assertEqual(data, {'other': 'abc'})


class TestDumpOnly(TestCase):
    def test_load_with_dump_only(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.IntegerField(dump_only=True)
            field_2 = serializers.IntegerField()

        data = {'field_1': 123, 'field_2': 456}

        self.assertEqual(Serializer().load(data), {'field_2': 456})

    def test_dump_with_dump_only(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.IntegerField(dump_only=True)
            field_2 = serializers.IntegerField()

        data = {'field_1': 123, 'field_2': 456}

        self.assertEqual(Serializer().dump(data), data)


class TestLoadFrom(TestCase):
    def test_load_from(self):
        class Serializer(serializers.Serializer):
            field = serializers.StringField(load_from='other')

        data = Serializer().load({'other': 'abc'})
        self.assertEqual(data, {'field': 'abc'})


class TestLoadOnly(TestCase):
    def test_dump_with_load_only(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.IntegerField(load_only=True)
            field_2 = serializers.IntegerField()

        data = {'field_1': 123, 'field_2': 456}

        self.assertEqual(Serializer().dump(data), {'field_2': 456})

    def test_load_with_load_only(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.IntegerField(load_only=True)
            field_2 = serializers.IntegerField()

        data = {'field_1': 123, 'field_2': 456}

        self.assertEqual(Serializer().load(data), data)


class TestPartial(TestCase):
    def test_required(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.IntegerField()
            field_2 = serializers.IntegerField()

        s = Serializer(partial=True)

        data = {'field_1': 123}

        self.assertEqual(s.load(data), data)

    def test_default(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.IntegerField()
            field_2 = serializers.IntegerField(default=456)

        s = Serializer(partial=True)

        data = {'field_1': 123}

        self.assertEqual(s.load(data), data)


class TestOnly(TestCase):
    def test_only_as_string(self):
        class Serializer(serializers.Serializer):
            pass

        with self.assertRaises(AssertionError) as exc_info:
            Serializer(only='field_1')
        self.assertEqual(str(exc_info.exception), '`only` has to be a list or tuple')

    def test_dump_with_only_fields(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.IntegerField()
            field_2 = serializers.IntegerField()

        data = {'field_1': 123, 'field_2': 456}
        expected = {'field_1': 123}

        s = Serializer(only=['field_1'])
        self.assertEqual(s.dump(data), expected)

    def test_load_with_only_fields(self):
        class Serializer(serializers.Serializer):
            field_1 = serializers.IntegerField()
            field_2 = serializers.IntegerField()

        data = {'field_1': 123, 'field_2': 456}
        expected = {'field_2': 456}

        s = Serializer(only=['field_2'])
        self.assertEqual(s.load(data), expected)


class TestErrorMessages(TestCase):
    def test_invalid_error_key(self):
        """
        If a field raises a validation error, but does not have a corresponding
        error message, then raise an appropriate assertion error.
        """

        class FailField(serializers.Field):
            def _load(self, value):
                self._fail('incorrect')

        class Serializer(serializers.Serializer):
            field = FailField()

        with self.assertRaises(AssertionError) as exc_info:
            Serializer().load({'field': 'value'})

        self.assertEqual(str(exc_info.exception),
                         'ValidationError raised by `FailField`, but error key '
                         '`incorrect` does not exist in the `error_messages` dictionary.')

    def test_dict_error_message(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField(error_messages={'invalid': {'message': 'error message', 'code': 123}})

        with self.assertRaises(ValidationError) as exc_info:
            Serializer().load({'field': 'value'})

        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('error message', code=123)]})


class TestValidators(TestCase):
    def test_validator_without_return(self):
        def validate(value):
            pass

        class Serializer(serializers.Serializer):
            field = serializers.IntegerField(validators=[validate])

        data = {'field': 123}

        self.assertEqual(Serializer().load(data), data)

    def test_validator_returning_true(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField(validators=[lambda x: True])

        data = {'field': 123}

        self.assertEqual(Serializer().load(data), data)

    def test_validator_returning_false(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField(validators=[lambda x: False])

        data = {'field': 123}

        with self.assertRaises(serializers.ValidationError) as exc_info:
            Serializer().load(data)
        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('Invalid value.')]})

    def test_validator_throwing_exception(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField(validators=[lambda x: 1 / 0])

        data = {'field': 123}

        with self.assertRaises(ZeroDivisionError) as exc_info:
            Serializer().load(data)
        self.assertEqual(str(exc_info.exception), 'division by zero')

    def test_validator_throwing_validation_error(self):
        def validate(value):
            raise serializers.ValidationError('Invalid value: ' + str(value))

        class Serializer(serializers.Serializer):
            field = serializers.IntegerField(validators=[validate])

        data = {'field': 123}

        with self.assertRaises(serializers.ValidationError) as exc_info:
            Serializer().load(data)
        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('Invalid value: 123')]})

    def test_validator_on_serializer_throwing_validation_error(self):
        def validate(value):
            raise serializers.ValidationError({'field': 'Invalid value: ' + str(value.get('field'))})

        class Serializer(serializers.Serializer):
            field = serializers.IntegerField()

        data = {'field': 123}

        with self.assertRaises(serializers.ValidationError) as exc_info:
            Serializer(validators=[validate]).load(data)
        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('Invalid value: 123')]})

    def test_validator_on_serializer_throwing_validation_error_without_field_name(self):
        def validate(value):
            raise serializers.ValidationError('Invalid value: ' + str(value.get('field')))

        class Serializer(serializers.Serializer):
            field = serializers.IntegerField()

        data = {'field': 123}

        with self.assertRaises(serializers.ValidationError) as exc_info:
            Serializer(validators=[validate]).load(data)
        self.assertEqual(exc_info.exception.message, {'_serializer': [ValidationError('Invalid value: 123')]})

    def test_multi_validator_throwing_validation_error(self):
        def validate1(value):
            raise serializers.ValidationError('Invalid value.')

        def validate2(value):
            raise serializers.ValidationError('Invalid value 2.')

        class Serializer(serializers.Serializer):
            field = serializers.IntegerField(validators=[validate1, validate2])

        data = {'field': 123}

        with self.assertRaises(serializers.ValidationError) as exc_info:
            Serializer().load(data)
        self.assertEqual(exc_info.exception.message,
                         {'field': [ValidationError('Invalid value.'), ValidationError('Invalid value 2.')]})

    def test_multi_validator_on_serializer_throwing_validation_error(self):
        def validate1(value):
            raise serializers.ValidationError({'field': 'Invalid value.'})

        def validate2(value):
            raise serializers.ValidationError({'field': 'Invalid value 2.'})

        class Serializer(serializers.Serializer):
            field = serializers.IntegerField()

        data = {'field': 123}

        with self.assertRaises(serializers.ValidationError) as exc_info:
            Serializer(validators=[validate1, validate2]).load(data)
        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('Invalid value.')]})


class TestPost(TestCase):
    def test_post_dump(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField()

            def post_dump(self, data, original_data):
                data['field'] = 1
                return data

        self.assertEqual(Serializer().dump({'field': 123}), {'field': 1})

    def test_post_dumps(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField()

            def post_dumps(self, data, original_data):
                return {'result': data}

        data = [{'field': 123}]
        result = {'result': [{'field': 123}]}

        self.assertEqual(Serializer().dumps(data), result)

    def test_post_load(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField()

            def post_load(self, data, original_data):
                data['field'] = 1
                return data

        self.assertEqual(Serializer().load({'field': 123}), {'field': 1})

    def test_post_loads(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField()

            def post_loads(self, data, original_data):
                data[0]['field'] = 1
                return data

        data = [{'field': 123}]
        result = [{'field': 1}]

        self.assertEqual(Serializer().loads(data), result)

    def test_post_validate(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField()

            def post_validate(self, data):
                raise serializers.ValidationError({'field': ['Invalid value']})

        with self.assertRaises(serializers.ValidationError) as exc_info:
            Serializer().load({'field': 1})
        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('Invalid value')]})


class TestDump(TestCase):
    def test_dump_with_dict(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField()

        data = {'field': 123}
        expected = {'field': 123}
        self.assertEqual(Serializer().dump(data), expected)

    def test_dump_with_error(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField()

        data = {'field': 'value'}

        with self.assertRaises(ValueError):
            Serializer().dump(data)

    def test_dump_with_model(self):
        class Model(object):
            field = 123

        class Serializer(serializers.Serializer):
            field = serializers.IntegerField()

        output = Serializer().dump(Model())

        self.assertEqual(output, {'field': 123})

    def test_dumps(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField()

        data = [{'field': 123}]
        expected = [{'field': 123}]
        self.assertEqual(Serializer().dumps(data), expected)


class TestLoad(TestCase):
    def test_load_with_dict(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField()

        data = {'field': 123}
        expected = {'field': 123}
        self.assertEqual(Serializer().load(data), expected)

    def test_load_with_error(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField()

        data = {'field': 'value'}

        with self.assertRaises(serializers.ValidationError) as exc_info:
            Serializer().load(data)
        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('A valid integer is required.')]})

    def test_load_with_model(self):
        class Model(object):
            field = 123

        class Serializer(serializers.Serializer):
            field = serializers.IntegerField()

        with self.assertRaises(serializers.ValidationError) as exc_info:
            Serializer().load(Model())
        self.assertEqual(exc_info.exception.message, 'Invalid data. Expected a dictionary, but got Model.')

    def test_loads(self):
        class Serializer(serializers.Serializer):
            field = serializers.IntegerField()

        data = [{'field': 123}]
        expected = [{'field': 123}]
        self.assertEqual(Serializer().loads(data), expected)


class TestView(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.client = self.app.test_client()

    def test_single_result(self):
        class Serializer(serializers.Serializer):
            field = serializers.StringField()

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
            field = serializers.StringField()

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
            field = serializers.StringField()

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
            field = serializers.StringField()

        @route('/view')
        @serializer(Serializer, envelope='results')
        def view():
            return None

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b'')


class TestHTMLInput(TestCase):
    def test_missing_html_integerfield(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.IntegerField()

        with self.assertRaises(serializers.ValidationError):
            TestSerializer().load(MultiDict())

    def test_missing_html_integerfield_with_default(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.IntegerField(default=123)

        data = TestSerializer().load(MultiDict())

        self.assertEqual(data, {'message': 123})

    def test_missing_html_stringfield(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.StringField()

        with self.assertRaises(serializers.ValidationError):
            TestSerializer().load(MultiDict())

    def test_missing_html_stringfield_with_default(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.StringField(default='happy')

        data = TestSerializer().load(MultiDict())

        self.assertEqual(data, {'message': 'happy'})

    def test_missing_html_listfield(self):
        class TestSerializer(serializers.Serializer):
            scores = serializers.ListField(serializers.IntegerField())

        with self.assertRaises(serializers.ValidationError):
            TestSerializer().load(MultiDict())

    def test_empty_html_integerfield(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.IntegerField()

        with self.assertRaises(serializers.ValidationError):
            TestSerializer().load(MultiDict({'message': ''}))

    def test_empty_html_integerfield_allow_none(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.IntegerField(allow_none=True)

        data = TestSerializer().load(MultiDict({'message': ''}))
        self.assertEqual(data, {'message': None})

    def test_empty_html_integerfield_required_false(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.IntegerField(required=False)

        data = TestSerializer().load(MultiDict({'message': ''}))
        self.assertEqual(data, {})

    def test_empty_html_stringfield(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.StringField()

        with self.assertRaises(serializers.ValidationError):
            TestSerializer().load(MultiDict({'message': ''}))

    def test_empty_html_stringfield_required_false(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.StringField(required=False)

        data = TestSerializer().load(MultiDict({'message': ''}))
        self.assertEqual(data, {})

    def test_empty_html_stringfield_with_allow_blank(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.StringField(allow_blank=True)

        data = TestSerializer().load(MultiDict({'message': ''}))
        self.assertEqual(data, {'message': ''})

    def test_empty_html_stringfield_allow_none(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.StringField(allow_none=True)

        data = TestSerializer().load(MultiDict({'message': ''}))
        self.assertEqual(data, {'message': None})

    def test_empty_html_stringfield_allow_none_allow_blank(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.StringField(allow_none=True, allow_blank=True)

        data = TestSerializer().load(MultiDict({'message': ''}))
        self.assertEqual(data, {'message': ''})

    def test_html_listfield(self):
        class TestSerializer(serializers.Serializer):
            scores = serializers.ListField(serializers.IntegerField())

        md = MultiDict()
        md.add('scores', 1)
        md.add('scores', 5)

        data = TestSerializer().load(md)
        self.assertEqual(data, {'scores': [1, 5]})


class FieldValues(object):
    """
    Base class for testing valid and invalid input values.
    """

    def get_items(self, mapping_or_list_of_two_tuples):
        # Tests accept either lists of two tuples, or dictionaries.
        if isinstance(mapping_or_list_of_two_tuples, dict):
            # {value: expected}
            return mapping_or_list_of_two_tuples.items()
        # [(value, expected), ...]
        return mapping_or_list_of_two_tuples

    def test_valid_inputs(self):
        """
        Ensure that valid values return the expected validated data.
        """
        for input_value, expected_output in self.get_items(self.valid_inputs):
            self.assertEqual(self.field.load(input_value), expected_output)

    def test_invalid_inputs(self):
        """
        Ensure that invalid values raise the expected validation error.
        """
        for input_value, expected_failure in self.get_items(self.invalid_inputs):
            with self.assertRaises(serializers.ValidationError) as exc_info:
                self.field.load(input_value)
            self.assertEqual(exc_info.exception.message, expected_failure)

    def test_outputs(self):
        for output_value, expected_output in self.get_items(self.outputs):
            self.assertEqual(self.field.dump(output_value), expected_output)


class TestBooleanField(TestCase, FieldValues):
    """
    Valid and invalid values for `BooleanField`.
    """
    valid_inputs = {
        'true': True,
        'false': False,
        '1': True,
        '0': False,
        1: True,
        0: False,
        True: True,
        False: False,
    }
    invalid_inputs = {
        'foo': '"foo" is not a valid boolean.',
    }
    outputs = {
        'true': True,
        'false': False,
        '1': True,
        '0': False,
        1: True,
        0: False,
        True: True,
        False: False,
        'other': True,
        None: None
    }
    field = serializers.BooleanField()

    def test_unhashable_types(self):
        inputs = (
            [],
            {},
        )
        field = serializers.BooleanField()
        for input_value in inputs:
            with self.assertRaises(serializers.ValidationError) as exc_info:
                field.load(input_value)
            expected = '"{0}" is not a valid boolean.'.format(input_value)
            self.assertEqual(exc_info.exception.message, expected)


class TestDateField(TestCase, FieldValues):
    """
    Valid and invalid values for `DateField`.
    """
    valid_inputs = {
        '2001-01-01': datetime.date(2001, 1, 1),
        datetime.date(2001, 1, 1): datetime.date(2001, 1, 1),
    }
    invalid_inputs = {
        'abc': 'Date has wrong format.',
        '2001-99-99': 'Date has wrong format.',
        datetime.datetime(2001, 1, 1, 12, 00): 'Expected a date but got a datetime.',
    }
    outputs = {
        datetime.date(2001, 1, 1): '2001-01-01',
        None: None,
    }
    field = serializers.DateField()


class TestDateTimeField(TestCase, FieldValues):
    """
    Valid and invalid values for `DateTimeField`.
    """
    valid_inputs = {
        '2001-01-01 13:00': datetime.datetime(2001, 1, 1, 13, 00, tzinfo=timezone.UTC()),
        '2001-01-01T13:00': datetime.datetime(2001, 1, 1, 13, 00, tzinfo=timezone.UTC()),
        '2001-01-01T13:00Z': datetime.datetime(2001, 1, 1, 13, 00, tzinfo=timezone.UTC()),
        datetime.datetime(2001, 1, 1, 13, 00): datetime.datetime(2001, 1, 1, 13, 00, tzinfo=timezone.UTC()),
        datetime.datetime(2001, 1, 1, 13, 00, tzinfo=timezone.UTC()): datetime.datetime(2001, 1, 1, 13, 00,
                                                                                        tzinfo=timezone.UTC()),
    }
    invalid_inputs = {
        'abc': 'Datetime has wrong format.',
        '2001-99-99T99:00': 'Datetime has wrong format.',
        datetime.date(2001, 1, 1): 'Expected a datetime but got a date.',
    }
    outputs = {
        datetime.datetime(2001, 1, 1, 13, 00): '2001-01-01T13:00:00',
        datetime.datetime(2001, 1, 1, 13, 00, tzinfo=timezone.UTC()): '2001-01-01T13:00:00Z',
        None: None,
    }
    field = serializers.DateTimeField(default_timezone=timezone.UTC())


class TestNaiveDateTimeField(TestCase, FieldValues):
    """
    Valid and invalid values for `DateTimeField` with naive datetimes.
    """
    valid_inputs = {
        datetime.datetime(2001, 1, 1, 13, 00): datetime.datetime(2001, 1, 1, 13, 00),
        datetime.datetime(2001, 1, 1, 13, 00, tzinfo=timezone.UTC()): datetime.datetime(2001, 1, 1, 13, 00,
                                                                                        tzinfo=timezone.UTC()),
        '2001-01-01 13:00': datetime.datetime(2001, 1, 1, 13, 00),
    }
    invalid_inputs = {}
    outputs = {}
    field = serializers.DateTimeField(default_timezone=None)


class TestDecimalField(TestCase, FieldValues):
    """
    Valid and invalid values for `DecimalField`.
    """
    valid_inputs = {
        '12.3': Decimal('12.3'),
        '0.1': Decimal('0.1'),
        10: Decimal('10'),
        0: Decimal('0'),
        12.3: Decimal('12.3'),
        0.1: Decimal('0.1'),
        '2E+1': Decimal('20'),
    }
    invalid_inputs = {
        'abc': 'A valid number is required.',
        Decimal('Nan'): 'A valid number is required.',
        Decimal('Inf'): 'A valid number is required.',
        '12.345': 'Ensure that there are no more than 3 digits in total.',
        200000000000.0: 'Ensure that there are no more than 3 digits in total.',
        '0.01': 'Ensure that there are no more than 1 decimal places.',
        123: 'Ensure that there are no more than 2 digits before the decimal point.',
        '2E+2': 'Ensure that there are no more than 2 digits before the decimal point.',
        ''.join('a' for i in range(1001)): 'String value too large.'

    }
    outputs = {
        '1': '1.0',
        '0': '0.0',
        '1.09': '1.1',
        '0.04': '0.0',
        1: '1.0',
        0: '0.0',
        Decimal('1.0'): '1.0',
        Decimal('0.0'): '0.0',
        Decimal('1.09'): '1.1',
        Decimal('0.04'): '0.0',
        None: None,
    }
    field = serializers.DecimalField(max_digits=3, decimal_places=1)

    def test_no_limits(self):
        input_value = 200000000000.12
        expected_value = Decimal('200000000000.12')

        field = serializers.DecimalField()
        data = field.load(input_value)

        self.assertEqual(data, expected_value)


class TestMinMaxDecimalField(TestCase, FieldValues):
    """
    Valid and invalid values for `DecimalField` with min and max limits.
    """
    valid_inputs = {
        '10.0': Decimal('10.0'),
        '20.0': Decimal('20.0'),
    }
    invalid_inputs = {
        '9.9': 'Ensure this value is greater than or equal to 10.',
        '20.1': 'Ensure this value is less than or equal to 20.',
    }
    outputs = {}
    field = serializers.DecimalField(max_digits=3, decimal_places=1, min_value=10, max_value=20)


class TestIntegerField(TestCase, FieldValues):
    """
    Valid and invalid values for `IntegerField`.
    """
    valid_inputs = {
        '1': 1,
        '0': 0,
        1: 1,
        0: 0,
        1.0: 1,
        0.0: 0,
    }
    invalid_inputs = {
        'abc': 'A valid integer is required.',
        '1.0': 'A valid integer is required.',
        ''.join('a' for i in range(1001)): 'String value too large.'
    }
    outputs = {
        '1': 1,
        '0': 0,
        1: 1,
        0: 0,
        1.0: 1,
        0.0: 0,
        None: None
    }
    field = serializers.IntegerField()

    def test_empty_html_with_default(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.IntegerField(default=123)

        data = TestSerializer().load(MultiDict({'message': ''}))

        self.assertEqual(data, {'message': 123})


class TestMinMaxIntegerField(TestCase, FieldValues):
    """
    Valid and invalid values for `IntegerField` with min and max limits.
    """
    valid_inputs = {
        '1': 1,
        '3': 3,
        1: 1,
        3: 3,
    }
    invalid_inputs = {
        0: 'Must be at least 1.',
        4: 'Must be at most 3.',
        '0': 'Must be at least 1.',
        '4': 'Must be at most 3.',
    }
    outputs = {}
    field = serializers.IntegerField(min_value=1, max_value=3)


class TestFloatField(TestCase, FieldValues):
    """
    Valid and invalid values for `FloatField`.
    """
    valid_inputs = {
        '1': 1.0,
        '0': 0.0,
        1: 1.0,
        0: 0.0,
        1.0: 1.0,
        0.0: 0.0,
    }
    invalid_inputs = {
        'abc': 'A valid number is required.',
        ''.join('a' for i in range(1001)): 'String value too large.'

    }
    outputs = {
        '1': 1.0,
        '0': 0.0,
        1: 1.0,
        0: 0.0,
        1.0: 1.0,
        0.0: 0.0,
        None: None
    }
    field = serializers.FloatField()


class TestMinMaxFloatField(TestCase, FieldValues):
    """
    Valid and invalid values for `FloatField` with min and max limits.
    """
    valid_inputs = {
        '1': 1,
        '3': 3,
        1: 1,
        3: 3,
        1.0: 1.0,
        3.0: 3.0,
    }
    invalid_inputs = {
        0.9: 'Ensure this value is greater than or equal to 1.',
        3.1: 'Ensure this value is less than or equal to 3.',
        '0.0': 'Ensure this value is greater than or equal to 1.',
        '3.1': 'Ensure this value is less than or equal to 3.',
    }
    outputs = {}
    field = serializers.FloatField(min_value=1, max_value=3)


class TestDelimitedListField(TestCase, FieldValues):
    """
    Values for `DelimitedListField` with IntegerField as child.
    """
    valid_inputs = [
        ('', []),
        ('1', [1]),
        ('1,2,3', [1, 2, 3]),
    ]
    invalid_inputs = [
        ('one, two', 'A valid integer is required.'),
        ([], 'A valid string is required.'),
    ]
    outputs = [
        ([1, 2, 3], '1,2,3'),
        (['1', '2', '3'], '1,2,3'),
        (None, None)
    ]
    field = serializers.DelimitedListField(serializers.IntegerField())

    def test_disallow_empty(self):
        field = serializers.DelimitedListField(serializers.IntegerField(), allow_empty=False)
        with self.assertRaises(serializers.ValidationError):
            field.load('')


class TestListField(TestCase, FieldValues):
    """
    Values for `ListField` with IntegerField as child.
    """
    valid_inputs = [
        ([1, 2, 3], [1, 2, 3]),
        (['1', '2', '3'], [1, 2, 3]),
        ([], [])
    ]
    invalid_inputs = [
        ('not a list', 'Not a valid list.'),
        ([1, 2, 'error'], {2: [ValidationError('A valid integer is required.')]}),
        ({'one': 'two'}, 'Not a valid list.')
    ]
    outputs = [
        ([1, 2, 3], [1, 2, 3]),
        (['1', '2', '3'], [1, 2, 3]),
        (None, None)
    ]
    field = serializers.ListField(serializers.IntegerField())

    def test_disallow_empty(self):
        field = serializers.ListField(serializers.IntegerField(), allow_empty=False)
        with self.assertRaises(serializers.ValidationError):
            field.load([])


class TestStringField(TestCase, FieldValues):
    """
    Valid and invalid values for `StringField`.
    """
    valid_inputs = {
        1: '1',
        'abc': 'abc'
    }
    invalid_inputs = {
        '': 'This field may not be blank.'
    }
    outputs = {
        1: '1',
        'abc': 'abc',
        None: None
    }
    field = serializers.StringField()

    def test_trim_whitespace_default(self):
        field = serializers.StringField()
        self.assertEqual(field.load(' abc '), 'abc')

    def test_trim_whitespace_disabled(self):
        field = serializers.StringField(trim_whitespace=False)
        self.assertEqual(field.load(' abc '), ' abc ')

    def test_disallow_blank_with_trim_whitespace(self):
        field = serializers.StringField(allow_blank=False, trim_whitespace=True)

        with self.assertRaises(serializers.ValidationError) as exc_info:
            field.load('   ')
        self.assertEqual(exc_info.exception.message, 'This field may not be blank.')


class TestMinMaxStringField(TestCase, FieldValues):
    """
    Valid and invalid values for `StringField` with min and max limits.
    """
    valid_inputs = {
        12: '12',
        'ab': 'ab',
        'abcd': 'abcd',
    }
    invalid_inputs = {
        '1': 'Shorter than minimum length 2.',
        1: 'Shorter than minimum length 2.',
        'abcde': 'Longer than maximum length 4.',
        12345: 'Longer than maximum length 4.',
    }
    outputs = {}
    field = serializers.StringField(min_length=2, max_length=4)


class TestUUIDField(TestCase, FieldValues):
    """
    Valid and invalid values for `UUIDField`.
    """
    valid_inputs = {
        '825d7aeb-05a9-45b5-a5b7-05df87923cda': uuid.UUID('825d7aeb-05a9-45b5-a5b7-05df87923cda'),
        '825d7aeb05a945b5a5b705df87923cda': uuid.UUID('825d7aeb-05a9-45b5-a5b7-05df87923cda'),
        uuid.UUID('825d7aeb-05a9-45b5-a5b7-05df87923cda'): uuid.UUID('825d7aeb-05a9-45b5-a5b7-05df87923cda')
    }
    invalid_inputs = {
        '825d7aeb-05a9-45b5-a5b7': '"825d7aeb-05a9-45b5-a5b7" is not a valid UUID.',
        (1, 2, 3): '"(1, 2, 3)" is not a valid UUID.',
        123: '"123" is not a valid UUID.',
    }
    outputs = {
        '825d7aeb-05a9-45b5-a5b7-05df87923cda': '825d7aeb-05a9-45b5-a5b7-05df87923cda',
        uuid.UUID('825d7aeb-05a9-45b5-a5b7-05df87923cda'): '825d7aeb-05a9-45b5-a5b7-05df87923cda',
        None: None
    }
    field = serializers.UUIDField()


if Enum:
    class TestEnumField(TestCase, FieldValues):
        """
        Valid and invalid values for `EnumField`.
        """
        class TestEnum(Enum):
            member1 = 1
            member2 = 2

        valid_inputs = {
            1: TestEnum.member1,
            2: TestEnum.member2,
            '1': TestEnum.member1,
            '2': TestEnum.member2,
            TestEnum.member2: TestEnum.member2,
        }
        invalid_inputs = {
            0: '"0" is not a valid choice.',
            3: '"3" is not a valid choice.',
            '3': '"3" is not a valid choice.',
        }
        outputs = {
            1: 1,
            2: 2,
            TestEnum.member2: 2,
            None: None
        }
        field = serializers.EnumField(TestEnum)
