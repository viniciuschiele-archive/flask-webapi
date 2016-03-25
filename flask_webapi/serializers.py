import datetime
import decimal
import uuid

from collections import OrderedDict
from werkzeug.utils import cached_property
from .exceptions import ValidationError
from .utils import dateparse, formatting, html, missing, timezone
from .validators import LengthValidator, RangeValidator


MISSING_ERROR_MESSAGE = 'ValidationError raised by `{class_name}`, but error key `{key}` does ' \
                        'not exist in the `error_messages` dictionary.'


class Field(object):
    default_error_messages = {
        'required': 'This field is required.',
        'null': 'This field may not be null.',
        'validator_failed': 'Invalid value.'
    }

    def __init__(self, dump_only=False, load_only=False, required=None, default=missing, allow_none=None,
                 dump_to=None, load_from=None, error_messages=None, validators=None):
        self.dump_only = dump_only
        self.load_only = load_only
        self.default = default
        self.allow_none = allow_none
        self.dump_to = dump_to
        self.load_from = load_from
        self.validators = validators or []

        # If `required` is unset, then use `True` unless a default is provided.
        if required is None:
            self.required = default is missing
        else:
            self.required = required

        if allow_none is None:
            self.allow_none = default is None
        else:
            self.allow_none = allow_none

        # Collect default error message from self and parent classes
        messages = {}
        for cls in reversed(self.__class__.__mro__):
            messages.update(getattr(cls, 'default_error_messages', {}))
        messages.update(error_messages or {})
        self.error_messages = messages

        self.field_name = None
        self.parent = None

    @cached_property
    def root(self):
        """
        Returns the top-level serializer for this field.
        """
        root = self
        while root.parent is not None:
            root = root.parent
        return root

    def bind(self, field_name, parent):
        self.field_name = field_name
        self.parent = parent

        if not self.dump_to:
            self.dump_to = field_name

        if not self.load_from:
            self.load_from = field_name

    def get_attribute(self, instance):
        if isinstance(instance, dict):
            return instance.get(self.field_name, missing)
        else:
            return getattr(instance, self.field_name, missing)

    def get_value(self, dictionary):
        value = dictionary.get(self.load_from, missing)

        if html.is_html_input(dictionary):
            if value == '' and self.allow_none:
                return None
            elif value == '' and not self.required:
                return missing
        return value

    def get_default(self):
        if callable(self.default):
            return self.default()
        return self.default

    def dump(self, value):
        if value is missing:
            return self.get_default()

        if value is None:
            return None

        return self._dump(value)

    def load(self, data):
        if data is missing:
            if getattr(self.root, 'partial', False):
                return missing

            if self.required:
                self._fail('required')

            return self.get_default()

        if data is None:
            if not self.allow_none:
                self._fail('null')
            return None

        validated_data = self._load(data)
        self._validate(validated_data)
        return validated_data

    def _dump(self, value):
        raise NotImplementedError()

    def _load(self, value):
        raise NotImplementedError()

    def _fail(self, key, **kwargs):
        try:
            message = self.error_messages[key]
            message = formatting.format_error_message(message, **kwargs)
            if isinstance(message, dict):
                raise ValidationError(**message)
            raise ValidationError(message)
        except KeyError:
            class_name = self.__class__.__name__
            message = formatting.format_error_message(MISSING_ERROR_MESSAGE, class_name=class_name, key=key)
            raise AssertionError(message)

    def _validate(self, data):
        errors = []
        for validator in self.validators:
            try:
                if validator(data) is False:
                    self._fail('validator_failed')
            except ValidationError as err:
                if isinstance(err.message, dict):
                    raise

                errors.append(err)

        if errors:
            raise ValidationError(errors)


class BooleanField(Field):
    default_error_messages = {
        'invalid': '"{value}" is not a valid boolean.'
    }

    TRUE_VALUES = {'t', 'T', 'true', 'True', 'TRUE', '1', 1, True}
    FALSE_VALUES = {'f', 'F', 'false', 'False', 'FALSE', '0', 0, 0.0, False}

    def _load(self, value):
        try:
            if value in self.TRUE_VALUES:
                return True
            if value in self.FALSE_VALUES:
                return False
        except TypeError:
            pass
        self._fail('invalid', value=value)

    def _dump(self, value):
        if value in self.TRUE_VALUES:
            return True
        if value in self.FALSE_VALUES:
            return False
        return bool(value)


class DateField(Field):
    default_error_messages = {
        'invalid': 'Date has wrong format.',
        'datetime': 'Expected a date but got a datetime.',
    }

    def _load(self, value):
        if isinstance(value, datetime.datetime):
            self._fail('datetime')

        if isinstance(value, datetime.date):
            return value

        try:
            parsed = dateparse.parse_date(value)
            if parsed is not None:
                return parsed
        except (ValueError, TypeError):
            pass

        self._fail('invalid')

    def _dump(self, value):
        return value.isoformat()


class DateTimeField(Field):
    default_error_messages = {
        'invalid': 'Datetime has wrong format.',
        'date': 'Expected a datetime but got a date.',
    }

    default_timezone = None

    def __init__(self, default_timezone=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if default_timezone is not None:
            self.default_timezone = default_timezone

    def _load(self, value):
        if isinstance(value, datetime.datetime):
            return self._enforce_timezone(value)

        if isinstance(value, datetime.date):
            self._fail('date')

        try:
            parsed = dateparse.parse_datetime(value)
            if parsed is not None:
                return self._enforce_timezone(parsed)
        except (ValueError, TypeError):
            pass

        self._fail('invalid')

    def _dump(self, value):
        value = value.isoformat()
        if value.endswith('+00:00'):
            value = value[:-6] + 'Z'
        return value

    def _enforce_timezone(self, value):
        """
        When `self.default_timezone` is `None`, always return naive datetimes.
        When `self.default_timezone` is not `None`, always return aware datetimes.
        """
        if self.default_timezone is not None and not timezone.is_aware(value):
            return timezone.make_aware(value, self.default_timezone)
        return value


class DecimalField(Field):
    default_error_messages = {
        'invalid': 'A valid number is required.',
        'max_value': 'Ensure this value is less than or equal to {max_value}.',
        'min_value': 'Ensure this value is greater than or equal to {min_value}.',
        'max_digits': 'Ensure that there are no more than {max_digits} digits in total.',
        'max_decimal_places': 'Ensure that there are no more than {max_decimal_places} decimal places.',
        'max_whole_digits': 'Ensure that there are no more than {max_whole_digits} digits before the decimal point.',
        'max_string_length': 'String value too large.'
    }

    MAX_STRING_LENGTH = 1000  # Guard against malicious string inputs.

    def __init__(self, max_digits=None, decimal_places=None, max_value=None, min_value=None, **kwargs):
        super(DecimalField, self).__init__(**kwargs)

        self.max_digits = max_digits
        self.decimal_places = decimal_places

        self.max_value = max_value
        self.min_value = min_value

        if self.max_digits is not None and self.decimal_places is not None:
            self.max_whole_digits = self.max_digits - self.decimal_places
        else:
            self.max_whole_digits = None

        if self.min_value is not None or self.max_value is not None:
            self.validators.append(RangeValidator(min_value, max_value, self.error_messages))

    def _load(self, value):
        """
        Validate that the input is a decimal number and return a Decimal
        instance.
        :param value: The value to be decoded.
        """
        value = str(value)
        if len(value) > self.MAX_STRING_LENGTH:
            self._fail('max_string_length')

        try:
            value = decimal.Decimal(value)

            # Check for NaN and for infinity and negative infinity.
            if value.is_nan() or value.is_infinite():
                self._fail('invalid')

            return self._validate_precision(value)
        except decimal.DecimalException:
            self._fail('invalid')

    def _dump(self, value):
        if not isinstance(value, decimal.Decimal):
            value = decimal.Decimal(str(value))

        quantized = self._quantize(value)

        return '{0:f}'.format(quantized)

    def _quantize(self, value):
        """
        Quantize the decimal value to the configured precision.
        """
        context = decimal.getcontext().copy()
        context.prec = self.max_digits
        return value.quantize(
            decimal.Decimal('.1') ** self.decimal_places,
            context=context)

    def _validate_precision(self, value):
        """
        Ensure that there are no more than max_digits in the number, and no
        more than decimal_places digits after the decimal point.
        Override this method to disable the precision validation for input
        values or to enhance it in any way you need to.
        """
        sign, digittuple, exponent = value.as_tuple()

        if exponent >= 0:
            # 1234500.0
            total_digits = len(digittuple) + exponent
            whole_digits = total_digits
            decimal_places = 0
        elif len(digittuple) > abs(exponent):
            # 123.45
            total_digits = len(digittuple)
            whole_digits = total_digits - abs(exponent)
            decimal_places = abs(exponent)
        else:
            # 0.001234
            total_digits = abs(exponent)
            whole_digits = 0
            decimal_places = total_digits

        if self.max_digits is not None and total_digits > self.max_digits:
            self._fail('max_digits', max_digits=self.max_digits)
        if self.decimal_places is not None and decimal_places > self.decimal_places:
            self._fail('max_decimal_places', max_decimal_places=self.decimal_places)
        if self.max_whole_digits is not None and whole_digits > self.max_whole_digits:
            self._fail('max_whole_digits', max_whole_digits=self.max_whole_digits)

        return value


class DelimitedListField(Field):
    """
    A delimited list composed with another `Field` class that loads from a delimited string.
    """

    default_error_messages = {
        'invalid': 'A valid string is required.',
        'empty': 'This list may not be empty.'
    }

    delimiter = ','

    def __init__(self, child, allow_empty=True, delimiter=None, **kwargs):
        """
        Initializes a new instance of `DelimitedList`.
        :param Field child: A field instance.
        :param str delimiter: Delimiter between values.
        """
        super().__init__(**kwargs)
        self.child = child
        self.allow_empty = allow_empty
        self.delimiter = delimiter or self.delimiter

    def _load(self, value):
        if not isinstance(value, str):
            self._fail('invalid')

        if value == '':
            values = []
        else:
            values = value.split(self.delimiter)

        if not self.allow_empty and len(value) == 0:
            self._fail('empty')

        return [self.child.load(v) for v in values]

    def _dump(self, value):
        values = [self.child.dump(item) for item in value]
        return self.delimiter.join(str(v) for v in values)


class EnumField(Field):
    """
    A field that provides a set of enumerated values which an attribute must be constrained to.
    """

    default_error_messages = {
        'invalid': '"{value}" is not a valid choice.'
    }

    def __init__(self, enum_type, **kwargs):
        super().__init__(**kwargs)
        self.enum_type = enum_type

        # we get the type of the first member
        # to convert the input value to this format.
        # if we don't convert it will raise an
        # exception if the input value type is not the
        # same as member type.
        self.member_type = type(list(self.enum_type)[0].value)

    def _load(self, value):
        try:
            if type(value) is self.enum_type:
                return value

            # converts the input value to make sure
            # it is the same type as the member's type
            member_value = self.member_type(value)

            return self.enum_type(member_value)
        except (ValueError, TypeError):
            self._fail('invalid', value=value)

    def _dump(self, value):
        if type(value) is self.enum_type:
            return value.value

        # converts the input value to make sure
        # it is the same type as the member's type
        value = self.member_type(value)

        return self.enum_type(value).value


class IntegerField(Field):
    default_error_messages = {
        'invalid': 'A valid integer is required.',
        'max_value': 'Must be at most {max_value}.',
        'min_value': 'Must be at least {min_value}.',
        'max_string_length': 'String value too large.'
    }

    MAX_STRING_LENGTH = 1000  # Guard against malicious string inputs.

    def __init__(self, min_value=None, max_value=None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value

        if self.min_value is not None or self.max_value is not None:
            self.validators.append(RangeValidator(min_value, max_value, self.error_messages))

    def _load(self, value):
        if isinstance(value, str) and len(value) > self.MAX_STRING_LENGTH:
            self._fail('max_string_length')

        try:
            return int(value)
        except (ValueError, TypeError):
            self._fail('invalid')

    def _dump(self, value):
        return int(value)


class FloatField(Field):
    default_error_messages = {
        'invalid': 'A valid number is required.',
        'max_value': 'Ensure this value is less than or equal to {max_value}.',
        'min_value': 'Ensure this value is greater than or equal to {min_value}.',
        'max_string_length': 'String value too large.'
    }

    MAX_STRING_LENGTH = 1000  # Guard against malicious string inputs.

    def __init__(self, min_value=None, max_value=None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value

        if self.min_value is not None or self.max_value is not None:
            self.validators.append(RangeValidator(min_value, max_value, self.error_messages))

    def _load(self, value):
        if isinstance(value, str) and len(value) > self.MAX_STRING_LENGTH:
            self._fail('max_string_length')

        try:
            return float(value)
        except (TypeError, ValueError):
            self._fail('invalid')

    def _dump(self, value):
        return float(value)


class ListField(Field):
    default_error_messages = {
        'invalid': 'Not a valid list.',
        'empty': 'This list may not be empty.'
    }

    def __init__(self, child, allow_empty=True, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.child = child
        self.allow_empty = allow_empty

    def get_value(self, dictionary):
        value = dictionary.get(self.load_from, missing)

        if value == missing:
            return value

        if html.is_html_input(dictionary):
            value = dictionary.getlist(self.load_from)

        return value

    def _load(self, value):
        """
        List of dicts of native values <- List of dicts of primitive datatypes.
        """
        if not isinstance(value, list):
            self._fail('invalid')

        if not self.allow_empty and len(value) == 0:
            self._fail('empty')

        result = []
        errors = {}

        for idx, item in enumerate(value):
            try:
                result.append(self.child.load(item))
            except ValidationError as e:
                errors[idx] = e

        if errors:
            raise ValidationError(errors)

        return result

    def _dump(self, value):
        """
        List of object instances -> List of dicts of primitive datatypes.
        """
        return [self.child.dump(item) for item in value]


class StringField(Field):
    default_error_messages = {
        'blank': 'This field may not be blank.',
        'max_length': 'Longer than maximum length {max_length}.',
        'min_length': 'Shorter than minimum length {min_length}.'
    }

    def __init__(self, allow_blank=False, trim_whitespace=True, min_length=None, max_length=None, **kwargs):
        super().__init__(**kwargs)
        self.allow_blank = allow_blank
        self.trim_whitespace = trim_whitespace
        self.min_length = min_length
        self.max_length = max_length

        if self.min_length is not None or self.max_length is not None:
            self.validators.append(
                LengthValidator(self.min_length, self.max_length, error_messages=self.error_messages))

    def get_value(self, dictionary):
        value = dictionary.get(self.load_from, missing)

        if html.is_html_input(dictionary):
            if value == '' and self.allow_none:
                return '' if self.allow_blank else None
            elif value == '' and not self.required:
                return '' if self.allow_blank else missing
        return value

    def _load(self, value):
        value = str(value)

        if self.trim_whitespace:
            value = value.strip()

        if value == '' and not self.allow_blank:
            if self.allow_none:
                return None
            self._fail('blank')

        return value

    def _dump(self, value):
        return str(value)


class UUIDField(Field):
    default_error_messages = {
        'invalid': '"{value}" is not a valid UUID.',
    }

    def _load(self, value):
        if isinstance(value, uuid.UUID):
            return value

        try:
            return uuid.UUID(hex=value)
        except (AttributeError, ValueError):
            self._fail('invalid', value=value)

    def _dump(self, value):
        return str(value)


class SerializerMeta(type):
    def __new__(mcs, name, bases, attrs):
        attrs['_declared_fields'] = mcs._get_declared_fields(bases, attrs)
        return super(SerializerMeta, mcs).__new__(mcs, name, bases, attrs)

    @classmethod
    def _get_declared_fields(mcs, bases, attrs):
        fields = []

        for attr_name, attr in list(attrs.items()):
            if isinstance(attr, Field):
                fields.append((attr_name, attr))

        for base in reversed(bases):
            if hasattr(base, '_declared_fields'):
                fields = list(base._declared_fields.items()) + fields

        return OrderedDict(fields)


class Serializer(Field, metaclass=SerializerMeta):
    default_error_messages = {
        'invalid': 'Invalid data. Expected a dictionary, but got {datatype}.'
    }

    def __init__(self, only=None, partial=False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        only = only or ()
        if not isinstance(only, (list, tuple)):
            raise AssertionError('`only` has to be a list or tuple')

        self.only = only or ()
        self.partial = partial

    @cached_property
    def fields(self):
        """
        A dictionary of {field_name: field_instance}.
        """
        # `fields` is evaluated lazily. We do this to ensure that we don't
        # have issues importing modules that use ModelSerializers as fields,
        # even if Django's app-loading stage has not yet run.
        ret = {}
        for field_name, field in self._declared_fields.items():
            field.bind(field_name, self)
            ret[field_name] = field
        return ret

    def loads(self, data):
        instance = [self.load(value) for value in data]
        return self.post_loads(instance, data)

    def dumps(self, instances):
        data = [self.dump(instance) for instance in instances]
        data = self.post_dumps(data, instances)
        return data

    def post_load(self, data, original_data):
        return data

    def post_loads(self, data, original_data):
        return data

    def post_dump(self, data, original_data):
        return data

    def post_dumps(self, data, original_data):
        return data

    def post_validate(self, data):
        pass

    @cached_property
    def _load_fields(self):
        lst = []

        for field in self.fields.values():
            if self.only and field.field_name not in self.only:
                continue

            if field.dump_only:
                continue

            lst.append(field)

        return lst

    @cached_property
    def _dump_fields(self):
        lst = []

        for field in self.fields.values():
            if self.only and field.field_name not in self.only:
                continue

            if field.load_only:
                continue

            lst.append(field)

        return lst

    def _load(self, data):
        if not isinstance(data, dict):
            self._fail('invalid', datatype=type(data).__name__)

        result = dict()
        errors = dict()

        for field in self._load_fields:
            try:
                value = field.get_value(data)
                value = field.load(value)
                if value is not missing:
                    result[field.field_name] = value
            except ValidationError as err:
                errors[field.field_name] = err

        if errors:
            raise ValidationError(errors)

        return self.post_load(result, data)

    def _dump(self, instance):
        result = dict()

        for field in self._dump_fields:
            value = field.get_attribute(instance)
            value = field.dump(value)

            if value is not missing:
                result[field.dump_to] = value

        return self.post_dump(result, instance)

    def _validate(self, data):
        errors = []

        try:
            super()._validate(data)
        except ValidationError as err:
            errors.append(err)

        try:
            self.post_validate(data)
        except ValidationError as err:
            errors.append(err)

        d = {}

        for error in errors:
            if isinstance(error.message, dict):
                d.update(error.message)
            else:
                d['_serializer'] = error

        if d:
            raise ValidationError(d)
