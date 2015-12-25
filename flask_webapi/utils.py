def get_attr_2(obj1, obj2, name):
    value = None

    if hasattr(obj1, name):
        value = getattr(obj1, name)

    if value is None and hasattr(obj2, name):
        value = getattr(obj2, name)

    return value


def get_attr_3(obj1, obj2, obj3, name):
    value = None

    if hasattr(obj1, name):
        value = getattr(obj1, name)

    if value is None and hasattr(obj2, name):
        value = getattr(obj2, name)

    if value is None and hasattr(obj3, name):
        value = getattr(obj3, name)

    return value


def unpack(value):
    data, status, headers = value + (None,) * (3 - len(value))
    return data, status, headers
