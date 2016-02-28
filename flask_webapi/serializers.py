import datetime
import uuid

from collections import OrderedDict
from .exceptions import ValidationError
from .utils import missing, dateparse, timezone
from .utils.cache import cached_property
from .validators import MaxValueValidator, MinValueValidator, MaxLengthValidator, MinLengthValidator


MISSING_ERROR_MESSAGE = (
    'ValidationError raised by `{class_name}`, but error key `{key}` does '
    'not exist in the `error_messages` dictionary.'
)


class Field(object):
    default_error_messages = {
        'required': 'This field is required.',
        'null': 'This field may not be null.'
    }

    def __init__(self, dump_only=False, load_only=False, required=False, default=missing, allow_none=None,
                 dump_to=None, load_from=None, error_messages=None, validators=None):
        self.dump_only = dump_only
        self.load_only = load_only
        self.required = required
        self.default = default
        self.allow_none = allow_none
        self.dump_to = dump_to
        self.load_from = load_from
        self.field_name = None
        self.validators = validators or []

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

    def bind(self, field_name):
        self.field_name = field_name

        if not self.dump_to:
            self.dump_to = field_name

        if not self.load_from:
            self.load_from = field_name

    def get_attribute(self, instance):
        if isinstance(instance, dict):
            return instance.get(self.field_name, self.default)

        return getattr(instance, self.field_name, self.default)

    def get_value(self, dictionary):
        return dictionary.get(self.load_from, missing)

    def get_default(self):
        if callable(self.default):
            return self.default()
        return self.default

    def serialize(self, value):
        raise NotImplementedError()

    def deserialize(self, data):
        raise NotImplementedError()

    def safe_deserialize(self, data):
        if data is missing:
            if self.required:
                self._fail('required')
            return self.get_default()

        if data is None:
            if not self.allow_none:
                self._fail('null')
            return None

        validated_data = self.deserialize(data)
        self._validate(validated_data)
        return validated_data

    def _fail(self, key, **kwargs):
        try:
            msg = self.error_messages[key]
            message_string = msg.format(**kwargs)
            raise ValidationError(message_string)
        except KeyError:
            class_name = self.__class__.__name__
            msg = MISSING_ERROR_MESSAGE.format(class_name=class_name, key=key)
            raise AssertionError(msg)

    def _validate(self, data):
        errors = []
        for validator in self.validators:
            try:
                if validator(data) is False:
                    self._fail('validator_failed')
            except ValidationError as err:
                if isinstance(err.message, dict):
                    errors.append(err.message)
                else:
                    errors.extend(err.message)
        if errors:
            raise ValidationError(errors)


class BooleanField(Field):
    default_error_messages = {
        'invalid': '"{input}" is not a valid boolean.'
    }

    TRUE_VALUES = {'t', 'T', 'true', 'True', 'TRUE', '1', 1, True}
    FALSE_VALUES = {'f', 'F', 'false', 'False', 'FALSE', '0', 0, 0.0, False}

    def deserialize(self, data):
        try:
            if data in self.TRUE_VALUES:
                return True
            if data in self.FALSE_VALUES:
                return False
        except TypeError:
            pass
        self._fail('invalid', input=data)

    def serialize(self, value):
        if value is None:
            return None
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

    def deserialize(self, data):
        if isinstance(data, datetime.datetime):
            self._fail('datetime')

        if isinstance(data, datetime.date):
            return data

        try:
            parsed = dateparse.parse_date(data)
            if parsed is not None:
                return parsed
        except (ValueError, TypeError):
            pass

        self._fail('invalid')

    def serialize(self, value):
        if value is None:
            return None

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

    def deserialize(self, data):
        if isinstance(data, datetime.datetime):
            return self._enforce_timezone(data)

        if isinstance(data, datetime.date):
            self._fail('date')

        try:
            parsed = dateparse.parse_datetime(data)
            if parsed is not None:
                return self._enforce_timezone(parsed)
        except (ValueError, TypeError):
            pass

        self._fail('invalid')

    def serialize(self, value):
        if value is None:
            return None

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

        if self.min_value is not None:
            message = self.error_messages['min_value'].format(min_value=self.min_value)
            self.validators.append(MinValueValidator(self.min_value, message=message))

        if self.max_value is not None:
            message = self.error_messages['max_value'].format(max_value=self.max_value)
            self.validators.append(MaxValueValidator(self.max_value, message=message))

    def deserialize(self, value):
        if isinstance(value, str) and len(value) > self.MAX_STRING_LENGTH:
            self._fail('max_string_length')

        try:
            return int(value)
        except (ValueError, TypeError):
            self._fail('invalid')

    def serialize(self, value):
        if value is None:
            return None
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

        if self.max_value is not None:
            message = self.error_messages['max_value'].format(max_value=self.max_value)
            self.validators.append(MaxValueValidator(self.max_value, message=message))

        if self.min_value is not None:
            message = self.error_messages['min_value'].format(min_value=self.min_value)
            self.validators.append(MinValueValidator(self.min_value, message=message))

    def deserialize(self, data):
        if isinstance(data, str) and len(data) > self.MAX_STRING_LENGTH:
            self._fail('max_string_length')

        try:
            return float(data)
        except (TypeError, ValueError):
            self._fail('invalid')

    def serialize(self, value):
        if value is None:
            return None
        return float(value)


class ListField(Field):
    default_error_messages = {
        'not_a_list': 'Expected a list of items but got type "{input_type}".',
        'empty': 'This list may not be empty.'
    }

    def __init__(self, child, allow_empty=True, *args, **kwargs):
        super(ListField, self).__init__(*args, **kwargs)

        self.child = child
        self.allow_empty = allow_empty
        # self.child.bind(field_name='', parent=self)

    def deserialize(self, data):
        """
        List of dicts of native values <- List of dicts of primitive datatypes.
        """
        if not isinstance(data, list):
            self._fail('not_a_list', input_type=type(data).__name__)

        if not self.allow_empty and len(data) == 0:
            self._fail('empty')

        return [self.child.safe_deserialize(item) for item in data]

    def serialize(self, data):
        """
        List of object instances -> List of dicts of primitive datatypes.
        """
        return [self.child.serialize(item) for item in data]


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

        if self.min_length is not None:
            message = self.error_messages['min_length'].format(min_length=self.min_length)
            self.validators.append(MinLengthValidator(self.min_length, message=message))

        if self.max_length is not None:
            message = self.error_messages['max_length'].format(max_length=self.max_length)
            self.validators.append(MaxLengthValidator(self.max_length, message=message))

    def deserialize(self, data):
        value = str(data)

        if self.trim_whitespace:
            value = value.strip()

        if value == '' and not self.allow_blank:
            if self.allow_none:
                return None
            self._fail('blank')

        return value

    def serialize(self, value):
        if value is None:
            return None
        return str(value)


class UUIDField(Field):
    default_error_messages = {
        'invalid': '"{value}" is not a valid UUID.',
    }

    def deserialize(self, data):
        if isinstance(data, uuid.UUID):
            return data

        try:
            return uuid.UUID(hex=data)
        except (AttributeError, ValueError):
            self._fail('invalid', value=data)

    def serialize(self, value):
        return str(value)


class SerializerMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        attrs['fields'] = mcs._get_fields(bases, attrs)
        return super(SerializerMetaclass, mcs).__new__(mcs, name, bases, attrs)

    @classmethod
    def _get_fields(mcs, bases, attrs):
        fields = []

        for attr_name, attr in list(attrs.items()):
            if isinstance(attr, Field):
                attr.bind(attr_name)
                fields.append((attr_name, attr))

        for base in reversed(bases):
            if hasattr(base, '_fields'):
                fields = list(base._fields.items()) + fields

        return OrderedDict(fields)


class Serializer(Field, metaclass=SerializerMetaclass):
    default_error_messages = {
        'invalid': 'Invalid data. Expected a dictionary, but got {datatype}.'
    }

    def __init__(self, only=(), many=False):
        super().__init__()
        self._fields = None
        self.only = only
        self.many = many

    def load(self, data):
        if self.many:
            return [self.safe_deserialize(value) for value in data]

        return self.safe_deserialize(data)

    def dump(self, obj):
        if self.many:
            return [self.serialize(value) for value in obj]

        return self.serialize(obj)

    def deserialize(self, data):
        if not isinstance(data, dict):
            message = self.error_messages['invalid'].format(datatype=type(data).__name__)
            raise ValidationError(message)

        result = dict()
        errors = OrderedDict()
        fields = self._deserializable_fields

        for field in fields:
            try:
                value = field.get_value(data)
                value = field.safe_deserialize(value)
                if value is not missing:
                    result[field.dump_to] = value
            except ValidationError as err:
                errors[field.field_name] = err.message

        if errors:
            raise ValidationError(errors)

        return result

    def serialize(self, instance):
        result = dict()
        fields = self._serializable_fields

        for field in fields:
            value = field.get_attribute(instance)

            if value is missing:
                value = field.default
            else:
                value = field.serialize(value)

            if value is not missing:
                result[field.field_name] = value

        return result

    @cached_property
    def _deserializable_fields(self):
        dump_fields = []

        for field in self.fields.values():
            if self.only and field.field_name not in self.only:
                continue

            if field.dump_only:
                continue

            dump_fields.append(field)

        return dump_fields

    @cached_property
    def _serializable_fields(self):
        load_fields = []

        for field in self.fields.values():
            if self.only and field.field_name not in self.only:
                continue

            if field.load_only:
                continue

            load_fields.append(field)

        return load_fields
