import datetime
import uuid

# PyPy does no support Enum
try:
    from enum import Enum
except ImportError:
    Enum = None

from decimal import Decimal
from flask import Flask, json
from flask_webapi import WebAPI, serialization
from flask_webapi.exceptions import ValidationError
from flask_webapi.routers import route
from flask_webapi.serialization import serialize
from flask_webapi.utils import timezone
from unittest import TestCase
from werkzeug.datastructures import MultiDict


class TestHTMLInput(TestCase):
    def test_missing_html_integerfield(self):
        class Schema(serialization.Schema):
            message = serialization.IntegerField()

        with self.assertRaises(ValidationError):
            Schema().load(MultiDict())

    def test_missing_html_integerfield_with_default(self):
        class Schema(serialization.Schema):
            message = serialization.IntegerField(default=123)

        data = Schema().load(MultiDict())

        self.assertEqual(data, {'message': 123})

    def test_missing_html_stringfield(self):
        class TestSerializer(serialization.Schema):
            message = serialization.StringField()

        with self.assertRaises(ValidationError):
            TestSerializer().load(MultiDict())

    def test_missing_html_stringfield_with_default(self):
        class TestSerializer(serialization.Schema):
            message = serialization.StringField(default='happy')

        data = TestSerializer().load(MultiDict())

        self.assertEqual(data, {'message': 'happy'})

    def test_missing_html_listfield(self):
        class TestSerializer(serialization.Schema):
            scores = serialization.ListField(serialization.IntegerField())

        with self.assertRaises(ValidationError):
            TestSerializer().load(MultiDict())

    def test_empty_html_integerfield(self):
        class TestSerializer(serialization.Schema):
            message = serialization.IntegerField()

        with self.assertRaises(ValidationError):
            TestSerializer().load(MultiDict({'message': ''}))

    def test_empty_html_integerfield_allow_none(self):
        class TestSerializer(serialization.Schema):
            message = serialization.IntegerField(allow_none=True)

        data = TestSerializer().load(MultiDict({'message': ''}))
        self.assertEqual(data, {'message': None})

    def test_empty_html_integerfield_required_false(self):
        class TestSerializer(serialization.Schema):
            message = serialization.IntegerField(required=False)

        data = TestSerializer().load(MultiDict({'message': ''}))
        self.assertEqual(data, {})

    def test_empty_html_stringfield(self):
        class Schema(serialization.Schema):
            message = serialization.StringField()

        with self.assertRaises(ValidationError):
            Schema().load(MultiDict({'message': ''}))

    def test_empty_html_stringfield_required_false(self):
        class Schema(serialization.Schema):
            message = serialization.StringField(required=False)

        data = Schema().load(MultiDict({'message': ''}))
        self.assertEqual(data, {})

    def test_empty_html_stringfield_with_allow_blank(self):
        class Schema(serialization.Schema):
            message = serialization.StringField(allow_blank=True)

        data = Schema().load(MultiDict({'message': ''}))
        self.assertEqual(data, {'message': ''})

    def test_empty_html_stringfield_allow_none(self):
        class Schema(serialization.Schema):
            message = serialization.StringField(allow_none=True)

        data = Schema().load(MultiDict({'message': ''}))
        self.assertEqual(data, {'message': None})

    def test_empty_html_stringfield_allow_none_allow_blank(self):
        class Schema(serialization.Schema):
            message = serialization.StringField(allow_none=True, allow_blank=True)

        data = Schema().load(MultiDict({'message': ''}))
        self.assertEqual(data, {'message': ''})

    def test_html_listfield(self):
        class Schema(serialization.Schema):
            scores = serialization.ListField(serialization.IntegerField())

        md = MultiDict()
        md.add('scores', 1)
        md.add('scores', 5)

        data = Schema().load(md)
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
            with self.assertRaises(ValidationError) as exc_info:
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
    field = serialization.BooleanField()

    def test_unhashable_types(self):
        inputs = (
            [],
            {},
        )
        field = serialization.BooleanField()
        for input_value in inputs:
            with self.assertRaises(ValidationError) as exc_info:
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
    field = serialization.DateField()


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
    field = serialization.DateTimeField(default_timezone=timezone.UTC())


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
    field = serialization.DateTimeField(default_timezone=None)


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
    field = serialization.DecimalField(max_digits=3, decimal_places=1)

    def test_no_limits(self):
        input_value = 200000000000.12
        expected_value = Decimal('200000000000.12')

        field = serialization.DecimalField()
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
    field = serialization.DecimalField(max_digits=3, decimal_places=1, min_value=10, max_value=20)


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
    field = serialization.IntegerField()

    def test_empty_html_with_default(self):
        class Schema(serialization.Schema):
            message = serialization.IntegerField(default=123)

        data = Schema().load(MultiDict({'message': ''}))

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
    field = serialization.IntegerField(min_value=1, max_value=3)


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
    field = serialization.FloatField()


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
    field = serialization.FloatField(min_value=1, max_value=3)


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
    field = serialization.DelimitedListField(serialization.IntegerField())

    def test_disallow_empty(self):
        field = serialization.DelimitedListField(serialization.IntegerField(), allow_empty=False)
        with self.assertRaises(ValidationError):
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
    field = serialization.ListField(serialization.IntegerField())

    def test_disallow_empty(self):
        field = serialization.ListField(serialization.IntegerField(), allow_empty=False)
        with self.assertRaises(ValidationError):
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
    field = serialization.StringField()

    def test_trim_whitespace_default(self):
        field = serialization.StringField()
        self.assertEqual(field.load(' abc '), 'abc')

    def test_trim_whitespace_disabled(self):
        field = serialization.StringField(trim_whitespace=False)
        self.assertEqual(field.load(' abc '), ' abc ')

    def test_disallow_blank_with_trim_whitespace(self):
        field = serialization.StringField(allow_blank=False, trim_whitespace=True)

        with self.assertRaises(ValidationError) as exc_info:
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
    field = serialization.StringField(min_length=2, max_length=4)


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
    field = serialization.UUIDField()


if Enum is not None:
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
        field = serialization.EnumField(TestEnum)


class TestNotImplemented(TestCase):
    def test_load(self):
        class Schema(serialization.Schema):
            field = serialization.Field()

        with self.assertRaises(NotImplementedError):
            Schema().load({'field': 123})

    def test_dump(self):
        class Schema(serialization.Schema):
            field = serialization.Field()

        with self.assertRaises(NotImplementedError):
            Schema().dump({'field': 123})


class TestAllowBlank(TestCase):
    def test_allow_blank(self):
        class Schema(serialization.Schema):
            field = serialization.StringField(allow_blank=True)

        data = {'field': ''}
        self.assertEqual(Schema().load(data), data)

    def test_disallow_blank(self):
        class Schema(serialization.Schema):
            field = serialization.StringField()

        with self.assertRaises(ValidationError) as exc_info:
            data = {'field': ''}
            self.assertEqual(Schema().load(data), data)

        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('This field may not be blank.')]})

    def test_disallow_blank_and_allow_none(self):
        class Schema(serialization.Schema):
            field = serialization.StringField(allow_none=True)

        data = {'field': ''}
        self.assertEqual(Schema().load(data), {'field': None})


class TestAllowNone(TestCase):
    def test_allow_none(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField(allow_none=True)

        data = {'field': None}
        self.assertEqual(Schema().load(data), data)

    def test_disallow_none(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField()

        with self.assertRaises(ValidationError) as exc_info:
            data = {'field': None}
            self.assertEqual(Schema().load(data), data)

        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('This field may not be null.')]})


class TestDefault(TestCase):
    def test_default_on_loading(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField(default=123)

        data = {}
        self.assertEqual(Schema().load(data), {'field': 123})

    def test_callable_default_on_loading(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField(default=lambda: 123)

        data = {}
        self.assertEqual(Schema().load(data), {'field': 123})

    def test_bypass_default_on_loading(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField(default=123)

        data = {'field': 456}
        self.assertEqual(Schema().load(data), {'field': 456})

    def test_default_on_dumping(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField(default=123)

        data = {}
        self.assertEqual(Schema().dump(data), {'field': 123})

    def test_default_missing_on_dumping(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField()

        data = {}
        self.assertEqual(Schema().dump(data), {})


class TestRequired(TestCase):
    def test_required(self):
        class Schema(serialization.Schema):
            field = serialization.StringField()

        data = {}
        with self.assertRaises(ValidationError):
            Schema().load(data)

        data = {'field': 'value'}
        self.assertEqual(Schema().load(data), data)

    def test_non_required(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField(required=False)

        data = {}
        self.assertEqual(Schema().load(data), data)


class TestDumpTo(TestCase):
    def test_dump_to(self):
        class Schema(serialization.Schema):
            field = serialization.StringField(dump_to='other')

        data = Schema().dump({'field': 'abc'})
        self.assertEqual(data, {'other': 'abc'})


class TestDumpOnly(TestCase):
    def test_load_with_dump_only(self):
        class Schema(serialization.Schema):
            field_1 = serialization.IntegerField(dump_only=True)
            field_2 = serialization.IntegerField()

        data = {'field_1': 123, 'field_2': 456}

        self.assertEqual(Schema().load(data), {'field_2': 456})

    def test_dump_with_dump_only(self):
        class Schema(serialization.Schema):
            field_1 = serialization.IntegerField(dump_only=True)
            field_2 = serialization.IntegerField()

        data = {'field_1': 123, 'field_2': 456}

        self.assertEqual(Schema().dump(data), data)


class TestLoadFrom(TestCase):
    def test_load_from(self):
        class Schema(serialization.Schema):
            field = serialization.StringField(load_from='other')

        data = Schema().load({'other': 'abc'})
        self.assertEqual(data, {'field': 'abc'})


class TestLoadOnly(TestCase):
    def test_dump_with_load_only(self):
        class Schema(serialization.Schema):
            field_1 = serialization.IntegerField(load_only=True)
            field_2 = serialization.IntegerField()

        data = {'field_1': 123, 'field_2': 456}

        self.assertEqual(Schema().dump(data), {'field_2': 456})

    def test_load_with_load_only(self):
        class Schema(serialization.Schema):
            field_1 = serialization.IntegerField(load_only=True)
            field_2 = serialization.IntegerField()

        data = {'field_1': 123, 'field_2': 456}

        self.assertEqual(Schema().load(data), data)


class TestPartial(TestCase):
    def test_required(self):
        class Schema(serialization.Schema):
            field_1 = serialization.IntegerField()
            field_2 = serialization.IntegerField()

        s = Schema(partial=True)

        data = {'field_1': 123}

        self.assertEqual(s.load(data), data)

    def test_default(self):
        class Schema(serialization.Schema):
            field_1 = serialization.IntegerField()
            field_2 = serialization.IntegerField(default=456)

        s = Schema(partial=True)

        data = {'field_1': 123}

        self.assertEqual(s.load(data), data)


class TestOnly(TestCase):
    def test_only_as_string(self):
        class Schema(serialization.Schema):
            pass

        with self.assertRaises(AssertionError) as exc_info:
            Schema(only='field_1')
        self.assertEqual(str(exc_info.exception), '`only` has to be a list or tuple')

    def test_dump_with_only_fields(self):
        class Schema(serialization.Schema):
            field_1 = serialization.IntegerField()
            field_2 = serialization.IntegerField()

        data = {'field_1': 123, 'field_2': 456}
        expected = {'field_1': 123}

        s = Schema(only=['field_1'])
        self.assertEqual(s.dump(data), expected)

    def test_load_with_only_fields(self):
        class Schema(serialization.Schema):
            field_1 = serialization.IntegerField()
            field_2 = serialization.IntegerField()

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

        class FailField(serialization.Field):
            def _load(self, value):
                self._fail('incorrect')

        class Schema(serialization.Schema):
            field = FailField()

        with self.assertRaises(AssertionError) as exc_info:
            Schema().load({'field': 'value'})

        self.assertEqual(str(exc_info.exception),
                         'ValidationError raised by `FailField`, but error key '
                         '`incorrect` does not exist in the `error_messages` dictionary.')

    def test_dict_error_message(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField(error_messages={'invalid': {'message': 'error message', 'code': 123}})

        with self.assertRaises(ValidationError) as exc_info:
            Schema().load({'field': 'value'})

        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('error message', code=123)]})


class TestValidators(TestCase):
    def test_validator_without_return(self):
        def validate(value):
            pass

        class Schema(serialization.Schema):
            field = serialization.IntegerField(validators=[validate])

        data = {'field': 123}

        self.assertEqual(Schema().load(data), data)

    def test_validator_returning_true(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField(validators=[lambda x: True])

        data = {'field': 123}

        self.assertEqual(Schema().load(data), data)

    def test_validator_returning_false(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField(validators=[lambda x: False])

        data = {'field': 123}

        with self.assertRaises(ValidationError) as exc_info:
            Schema().load(data)
        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('Invalid value.')]})

    def test_validator_throwing_exception(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField(validators=[lambda x: 1 / 0])

        data = {'field': 123}

        with self.assertRaises(ZeroDivisionError) as exc_info:
            Schema().load(data)
        self.assertEqual(str(exc_info.exception), 'division by zero')

    def test_validator_throwing_validation_error(self):
        def validate(value):
            raise ValidationError('Invalid value: ' + str(value))

        class Schema(serialization.Schema):
            field = serialization.IntegerField(validators=[validate])

        data = {'field': 123}

        with self.assertRaises(ValidationError) as exc_info:
            Schema().load(data)
        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('Invalid value: 123')]})

    def test_validator_on_serializer_throwing_validation_error(self):
        def validate(value):
            raise ValidationError({'field': 'Invalid value: ' + str(value.get('field'))})

        class Schema(serialization.Schema):
            field = serialization.IntegerField()

        data = {'field': 123}

        with self.assertRaises(ValidationError) as exc_info:
            Schema(validators=[validate]).load(data)
        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('Invalid value: 123')]})

    def test_validator_on_serializer_throwing_validation_error_without_field_name(self):
        def validate(value):
            raise ValidationError('Invalid value: ' + str(value.get('field')))

        class Schema(serialization.Schema):
            field = serialization.IntegerField()

        data = {'field': 123}

        with self.assertRaises(ValidationError) as exc_info:
            Schema(validators=[validate]).load(data)
        self.assertEqual(exc_info.exception.message, {'_serializer': [ValidationError('Invalid value: 123')]})

    def test_multi_validator_throwing_validation_error(self):
        def validate1(value):
            raise ValidationError('Invalid value.')

        def validate2(value):
            raise ValidationError('Invalid value 2.')

        class Schema(serialization.Schema):
            field = serialization.IntegerField(validators=[validate1, validate2])

        data = {'field': 123}

        with self.assertRaises(ValidationError) as exc_info:
            Schema().load(data)
        self.assertEqual(exc_info.exception.message,
                         {'field': [ValidationError('Invalid value.'), ValidationError('Invalid value 2.')]})

    def test_multi_validator_on_serializer_throwing_validation_error(self):
        def validate1(value):
            raise ValidationError({'field': 'Invalid value.'})

        def validate2(value):
            raise ValidationError({'field': 'Invalid value 2.'})

        class Schema(serialization.Schema):
            field = serialization.IntegerField()

        data = {'field': 123}

        with self.assertRaises(ValidationError) as exc_info:
            Schema(validators=[validate1, validate2]).load(data)
        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('Invalid value.')]})


class TestPost(TestCase):
    def test_post_dump(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField()

            def post_dump(self, data, original_data):
                data['field'] = 1
                return data

        self.assertEqual(Schema().dump({'field': 123}), {'field': 1})

    def test_post_dumps(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField()

            def post_dumps(self, data, original_data):
                return {'result': data}

        data = [{'field': 123}]
        result = {'result': [{'field': 123}]}

        self.assertEqual(Schema().dumps(data), result)

    def test_post_load(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField()

            def post_load(self, data, original_data):
                data['field'] = 1
                return data

        self.assertEqual(Schema().load({'field': 123}), {'field': 1})

    def test_post_loads(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField()

            def post_loads(self, data, original_data):
                data[0]['field'] = 1
                return data

        data = [{'field': 123}]
        result = [{'field': 1}]

        self.assertEqual(Schema().loads(data), result)

    def test_post_validate(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField()

            def post_validate(self, data):
                raise ValidationError({'field': ['Invalid value']})

        with self.assertRaises(ValidationError) as exc_info:
            Schema().load({'field': 1})
        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('Invalid value')]})


class TestDump(TestCase):
    def test_dump_with_dict(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField()

        data = {'field': 123}
        expected = {'field': 123}
        self.assertEqual(Schema().dump(data), expected)

    def test_dump_with_error(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField()

        data = {'field': 'value'}

        with self.assertRaises(ValueError):
            Schema().dump(data)

    def test_dump_with_model(self):
        class Model(object):
            field = 123

        class Schema(serialization.Schema):
            field = serialization.IntegerField()

        output = Schema().dump(Model())

        self.assertEqual(output, {'field': 123})

    def test_dumps(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField()

        data = [{'field': 123}]
        expected = [{'field': 123}]
        self.assertEqual(Schema().dumps(data), expected)


class TestLoad(TestCase):
    def test_load_with_dict(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField()

        data = {'field': 123}
        expected = {'field': 123}
        self.assertEqual(Schema().load(data), expected)

    def test_load_with_error(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField()

        data = {'field': 'value'}

        with self.assertRaises(ValidationError) as exc_info:
            Schema().load(data)
        self.assertEqual(exc_info.exception.message, {'field': [ValidationError('A valid integer is required.')]})

    def test_load_with_model(self):
        class Model(object):
            field = 123

        class Schema(serialization.Schema):
            field = serialization.IntegerField()

        with self.assertRaises(ValidationError) as exc_info:
            Schema().load(Model())
        self.assertEqual(exc_info.exception.message, 'Invalid data. Expected a dictionary, but got Model.')

    def test_loads(self):
        class Schema(serialization.Schema):
            field = serialization.IntegerField()

        data = [{'field': 123}]
        expected = [{'field': 123}]
        self.assertEqual(Schema().loads(data), expected)


class TestView(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.api = WebAPI(self.app)
        self.client = self.app.test_client()

    def test_single_result_with_many_none(self):
        class Schema(serialization.Schema):
            field = serialization.StringField()

        @route('/view')
        @serialize(Schema)
        def view():
            return {'field': 'value'}

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {'field': 'value'})

    def test_single_result_with_many_false(self):
        class Schema(serialization.Schema):
            field = serialization.StringField()

        @route('/view')
        @serialize(Schema, many=False)
        def view():
            return {'field': 'value'}

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(field='value'))

    def test_multiple_results_with_many_none(self):
        class Schema(serialization.Schema):
            field = serialization.StringField()

        @route('/view')
        @serialize(Schema)
        def view():
            return [{'field': 'value'}]

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), [dict(field='value')])

    def test_multiple_results_with_many_true(self):
        class Schema(serialization.Schema):
            field = serialization.StringField()

        @route('/view')
        @serialize(Schema, many=True)
        def view():
            return [{'field': 'value'}]

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), [dict(field='value')])

    def test_multiple_results_with_envelope(self):
        class Schema(serialization.Schema):
            field = serialization.StringField()

        @route('/view')
        @serialize(Schema, many=True, envelope='results')
        def view():
            return [{'field': 'value'}]

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), dict(results=[dict(field='value')]))

    def test_none_with_envelope(self):
        class Schema(serialization.Schema):
            field = serialization.StringField()

        @route('/view')
        @serialize(Schema, envelope='results')
        def view():
            return None

        self.api.add_view(view)
        response = self.client.get('/view')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b'')

    def test_fields_parameter(self):
        class Schema(serialization.Schema):
            first_name = serialization.StringField()
            last_name = serialization.StringField()
            age = serialization.IntegerField()

        @route('/view')
        @serialize(Schema)
        def view():
            return {'first_name': 'foo',
                    'last_name': 'bar',
                    'age': 30}

        self.api.add_view(view)
        response = self.client.get('/view?fields=last_name')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {'last_name': 'bar'})

    def test_fields_parameter_with_empty_value(self):
        class Schema(serialization.Schema):
            first_name = serialization.StringField()
            last_name = serialization.StringField()
            age = serialization.IntegerField()

        @route('/view')
        @serialize(Schema)
        def view():
            return {'first_name': 'foo',
                    'last_name': 'bar',
                    'age': 30}

        self.api.add_view(view)
        response = self.client.get('/view?fields=')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {'first_name': 'foo', 'last_name': 'bar', 'age': 30})

    def test_fields_parameter_with_invalid_field_name(self):
        class Schema(serialization.Schema):
            first_name = serialization.StringField()
            last_name = serialization.StringField()
            age = serialization.IntegerField()

        @route('/view')
        @serialize(Schema)
        def view():
            return {'first_name': 'foo',
                    'last_name': 'bar',
                    'age': 30}

        self.api.add_view(view)
        response = self.client.get('/view?fields=password')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {})
