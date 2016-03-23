from flask_webapi import validators
from flask_webapi.exceptions import ValidationError
from unittest import TestCase


class TestErrorMessages(TestCase):
    def test_invalid_error_key(self):
        """
        If a field raises a validation error, but does not have a corresponding
        error message, then raise an appropriate assertion error.
        """

        class FailValidator(validators.BaseValidator):
            def __call__(self):
                self._fail('incorrect')

        validator = FailValidator()

        with self.assertRaises(AssertionError) as exc_info:
            validator()
        self.assertEqual(str(exc_info.exception),
                         'ValidationError raised by `FailValidator`, but error key '
                         '`incorrect` does not exist in the `error_messages` dictionary.')

    def test_dict_error_message(self):
        error_messages = {'min_length': {'message': 'min size.', 'code': 123}}

        validator = validators.LengthValidator(min_length=2, error_messages=error_messages)

        with self.assertRaises(ValidationError) as exc_info:
            validator('a')

        self.assertEqual(exc_info.exception, ValidationError('min size.', code=123))


class ValidatorValues(object):
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
        for input_value in self.valid_inputs:
            self.validator(input_value)

    def test_invalid_inputs(self):
        """
        Ensure that invalid values raise the expected validation error.
        """
        for input_value in self.invalid_inputs:
            with self.assertRaises(ValidationError):
                self.validator(input_value)


class TestEmailValidator(TestCase, ValidatorValues):
    valid_inputs = (
        'niceandsimple@example.com',
        'NiCeAnDsImPlE@eXaMpLe.CoM',
        'very.common@example.com',
        'a.little.lengthy.but.fine@a.iana-servers.net',
        'disposable.style.email.with+symbol@example.com',
        '"very.unusual.@.unusual.com"@example.com',
        "!#$%&'*+-/=?^_`{}|~@example.org",
        'niceandsimple@[64.233.160.0]',
        'niceandsimple@localhost',
        u'josé@blah.com',
        u'δοκ.ιμή@παράδειγμα.δοκιμή',
    )

    invalid_inputs = [
        'a"b(c)d,e:f;g<h>i[j\\k]l@example.com',
        'just"not"right@example.com',
        'this is"not\allowed@example.com',
        'this\\ still\\"not\\\\allowed@example.com',
        '"much.more unusual"@example.com',
        '"very.(),:;<>[]\".VERY.\"very@\\ \"very\".unusual"@strange.example.com',
        '" "@example.org',
        'user@example',
        '@nouser.com',
        'example.com',
        'user',
        ''
        '',
        None,
    ]

    validator = validators.EmailValidator()


class TestLengthValidator(TestCase, ValidatorValues):
    valid_inputs = [
        'abcd',
        (1, 2, 3, 4),
        [1, 2, 3, 4],
        {'1': 1, '2': 2, '3': 3, '4': 4}
    ]

    invalid_inputs = [
        '1',
        '123456',
        (1,),
        [1,],
        {'1': 1},
    ]

    validator = validators.LengthValidator(min_length=3, max_length=5)

    def test_equal_length(self):
        self.assertEqual(validators.LengthValidator(equal_length=3)('123'), None)

        with self.assertRaises(ValidationError):
            validators.LengthValidator(equal_length=3)('1')

        with self.assertRaises(ValidationError):
            validators.LengthValidator(equal_length=3)('1234')

    def test_equal_length_with_min_length(self):
        with self.assertRaises(ValueError):
            validators.LengthValidator(min_length=1, equal_length=3)('foo')


class TestRangeValidator(TestCase, ValidatorValues):
    valid_inputs = [
        3,
        4,
        5,
    ]

    invalid_inputs = [
        2,
        6,
    ]

    validator = validators.RangeValidator(min_value=3, max_value=5)


class TestUUIDValidator(TestCase, ValidatorValues):
    valid_inputs = [
        '825d7aeb-05a9-45b5-a5b7-05df87923cda',
        '825d7aeb05a945b5a5b705df87923cda',
    ]

    invalid_inputs = [
        '825d7aeb-05a9-45b5-a5b7',
        (1, 2, 3),
        123,
    ]

    validator = validators.UUIDValidator()


class TestChoiceValidator(TestCase, ValidatorValues):
    valid_inputs = [
        1,
        2,
        3,
    ]

    invalid_inputs = [
        0,
        4,
        '1',
    ]

    validator = validators.ChoiceValidator([1, 2, 3])
