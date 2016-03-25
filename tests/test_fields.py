import datetime
import uuid

# PyPy does no support Enum
try:
    from enum import Enum
except ImportError:
    Enum = None

from decimal import Decimal
from flask_webapi import exceptions, fields, schemas
from flask_webapi.utils import timezone
from unittest import TestCase
from werkzeug.datastructures import MultiDict


class TestHTMLInput(TestCase):
    def test_missing_html_integerfield(self):
        class Schema(schemas.Schema):
            message = fields.IntegerField()

        with self.assertRaises(exceptions.ValidationError):
            Schema().load(MultiDict())

    def test_missing_html_integerfield_with_default(self):
        class Schema(schemas.Schema):
            message = fields.IntegerField(default=123)

        data = Schema().load(MultiDict())

        self.assertEqual(data, {'message': 123})

    def test_missing_html_stringfield(self):
        class TestSerializer(schemas.Schema):
            message = fields.StringField()

        with self.assertRaises(exceptions.ValidationError):
            TestSerializer().load(MultiDict())

    def test_missing_html_stringfield_with_default(self):
        class TestSerializer(schemas.Schema):
            message = fields.StringField(default='happy')

        data = TestSerializer().load(MultiDict())

        self.assertEqual(data, {'message': 'happy'})

    def test_missing_html_listfield(self):
        class TestSerializer(schemas.Schema):
            scores = fields.ListField(fields.IntegerField())

        with self.assertRaises(exceptions.ValidationError):
            TestSerializer().load(MultiDict())

    def test_empty_html_integerfield(self):
        class TestSerializer(schemas.Schema):
            message = fields.IntegerField()

        with self.assertRaises(exceptions.ValidationError):
            TestSerializer().load(MultiDict({'message': ''}))

    def test_empty_html_integerfield_allow_none(self):
        class TestSerializer(schemas.Schema):
            message = fields.IntegerField(allow_none=True)

        data = TestSerializer().load(MultiDict({'message': ''}))
        self.assertEqual(data, {'message': None})

    def test_empty_html_integerfield_required_false(self):
        class TestSerializer(schemas.Schema):
            message = fields.IntegerField(required=False)

        data = TestSerializer().load(MultiDict({'message': ''}))
        self.assertEqual(data, {})

    def test_empty_html_stringfield(self):
        class Schema(schemas.Schema):
            message = fields.StringField()

        with self.assertRaises(exceptions.ValidationError):
            Schema().load(MultiDict({'message': ''}))

    def test_empty_html_stringfield_required_false(self):
        class Schema(schemas.Schema):
            message = fields.StringField(required=False)

        data = Schema().load(MultiDict({'message': ''}))
        self.assertEqual(data, {})

    def test_empty_html_stringfield_with_allow_blank(self):
        class Schema(schemas.Schema):
            message = fields.StringField(allow_blank=True)

        data = Schema().load(MultiDict({'message': ''}))
        self.assertEqual(data, {'message': ''})

    def test_empty_html_stringfield_allow_none(self):
        class Schema(schemas.Schema):
            message = fields.StringField(allow_none=True)

        data = Schema().load(MultiDict({'message': ''}))
        self.assertEqual(data, {'message': None})

    def test_empty_html_stringfield_allow_none_allow_blank(self):
        class Schema(schemas.Schema):
            message = fields.StringField(allow_none=True, allow_blank=True)

        data = Schema().load(MultiDict({'message': ''}))
        self.assertEqual(data, {'message': ''})

    def test_html_listfield(self):
        class Schema(schemas.Schema):
            scores = fields.ListField(fields.IntegerField())

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
            with self.assertRaises(exceptions.ValidationError) as exc_info:
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
    field = fields.BooleanField()

    def test_unhashable_types(self):
        inputs = (
            [],
            {},
        )
        field = fields.BooleanField()
        for input_value in inputs:
            with self.assertRaises(exceptions.ValidationError) as exc_info:
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
    field = fields.DateField()


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
    field = fields.DateTimeField(default_timezone=timezone.UTC())


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
    field = fields.DateTimeField(default_timezone=None)


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
    field = fields.DecimalField(max_digits=3, decimal_places=1)

    def test_no_limits(self):
        input_value = 200000000000.12
        expected_value = Decimal('200000000000.12')

        field = fields.DecimalField()
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
    field = fields.DecimalField(max_digits=3, decimal_places=1, min_value=10, max_value=20)


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
    field = fields.IntegerField()

    def test_empty_html_with_default(self):
        class Schema(schemas.Schema):
            message = fields.IntegerField(default=123)

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
    field = fields.IntegerField(min_value=1, max_value=3)


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
    field = fields.FloatField()


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
    field = fields.FloatField(min_value=1, max_value=3)


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
    field = fields.DelimitedListField(fields.IntegerField())

    def test_disallow_empty(self):
        field = fields.DelimitedListField(fields.IntegerField(), allow_empty=False)
        with self.assertRaises(exceptions.ValidationError):
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
        ([1, 2, 'error'], {2: [exceptions.ValidationError('A valid integer is required.')]}),
        ({'one': 'two'}, 'Not a valid list.')
    ]
    outputs = [
        ([1, 2, 3], [1, 2, 3]),
        (['1', '2', '3'], [1, 2, 3]),
        (None, None)
    ]
    field = fields.ListField(fields.IntegerField())

    def test_disallow_empty(self):
        field = fields.ListField(fields.IntegerField(), allow_empty=False)
        with self.assertRaises(exceptions.ValidationError):
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
    field = fields.StringField()

    def test_trim_whitespace_default(self):
        field = fields.StringField()
        self.assertEqual(field.load(' abc '), 'abc')

    def test_trim_whitespace_disabled(self):
        field = fields.StringField(trim_whitespace=False)
        self.assertEqual(field.load(' abc '), ' abc ')

    def test_disallow_blank_with_trim_whitespace(self):
        field = fields.StringField(allow_blank=False, trim_whitespace=True)

        with self.assertRaises(exceptions.ValidationError) as exc_info:
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
    field = fields.StringField(min_length=2, max_length=4)


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
    field = fields.UUIDField()


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
        field = fields.EnumField(TestEnum)
