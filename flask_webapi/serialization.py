import copy
import inspect

from flask import request, current_app
from .filters import action_filter


@action_filter
def serializer(schema, many=None, envelope=None):
    """
    A decorator that apply a serializer to the action.
    :param Schema schema: The schema used to serialize the data.
    :param bool many: If set to `True` the object will be serialized to a list.
    :param str envelope: The key used to envelope the data.
    :return: A function.
    """
    schema = schema() if inspect.isclass(schema) else schema

    def serialize(func, *args, **kwargs):
        """
        Serializes the given data into a Python dict.
        :param func:
        :return: A Python dict object.
        """

        data = func(*args, **kwargs)

        if data is None:
            return None

        if data is current_app.response_class:
            return data

        local_schema = schema
        local_many = many

        # Gets the field names from the query string,
        # only those fields are going to be dumped.
        fields = request.args.get('fields')

        if fields:
            # schema has to be cloned to avoid
            # problem with multiple threads.
            local_schema = copy.copy(local_schema)
            local_schema.only = fields.split(',')
            local_schema.refresh()

        if local_many is None:
            local_many = isinstance(data, (list, tuple))

        if local_many:
            data = local_schema.dumps(data)
        else:
            data = local_schema.dump(data)

        if envelope:
            data = {envelope: data}

        return data

    return serialize
