class Missing(object):
    """
    This class is used to represent no data being provided for a given input
    or output value.
    It is required because `None` may be a valid input or output value.
    """
    pass


missing = Missing()


def unpack(value):
    data, status, headers = value + (None,) * (3 - len(value))
    return data, status, headers
