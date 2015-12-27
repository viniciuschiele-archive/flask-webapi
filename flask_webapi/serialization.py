"""
Serializers used to serialize a Python object into dict.
"""

from flask import request


def serializer(schema, envelope=None):
    """
    A decorator that apply marshalling to the return values of your methods.

    :param schema: The schema class to be used to serialize the values.
    :param envelope: The key used to envelope the data.
    :return: A function.
    """

    def decorator(func):
        func.serializer = schema
        func.envelope = envelope
        return func
    return decorator


def perform_serialization(data):
    """
    Serializes the given parameter into a Python dict.

    :param data: The data to be serialized.
    :return: A Python dict object.
    """

    if not request.action.serializer:
        return data

    if data is not None:
        fields = request.args.get('fields')
        if fields:
            fields = fields.split(',')
        else:
            fields = ()

        ser = request.action.get_serializer(fields=fields)

        many = isinstance(data, list)
        data = ser.dump(data, many=many).data

    envelope = request.action.envelope

    if envelope:
        data = {envelope: data}

    return data
