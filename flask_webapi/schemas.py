from collections import OrderedDict
from werkzeug.utils import cached_property
from .exceptions import ValidationError
from .fields import Field
from .utils import missing


class SchemaMeta(type):
    def __new__(mcs, name, bases, attrs):
        attrs['_declared_fields'] = mcs._get_declared_fields(bases, attrs)
        return super(SchemaMeta, mcs).__new__(mcs, name, bases, attrs)

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


class Schema(Field, metaclass=SchemaMeta):
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
