def get_attr(objects, name, default=None):
    missing = object()
    for obj in objects:
        value = getattr(obj, name, missing)
        if value != missing:
            return value
    return default


def unpack(value):
    data, status, headers = value + (None,) * (3 - len(value))
    return data, status, headers
