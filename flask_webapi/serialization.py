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
    if data is request.action.app.response_class:
        return data

    if request.action.serializer is None:
        return data

    if data is not None:
        fields = request.args.get('fields')
        if fields:
            only = fields.split(',')
        else:
            only = ()

        ser = request.action.get_serializer(only=only)

        many = isinstance(data, list)
        data = ser.dump(data, many=many).data

    envelope = request.action.envelope

    if envelope:
        data = {envelope: data}

    return data
