"""
Provides helper functions to deal with inspection and reflection.
"""

import inspect


def has_self_parameter(func):
    """
    Checks whether the given func has a self parameter.
    :param func: The func to be checked.
    :return: True if the func has the self parameter.
    """
    func_args = inspect.getargspec(func).args
    return len(func_args) > 0 and func_args[0] == 'self'


def func_to_method(func):
    """
    Converts a function to a method.
    :param func: The function to be converted.
    :return: A method.
    """
    def handle(_, *args, **kwargs):
        return func(*args, **kwargs)

    handle.__dict__ = func.__dict__

    return handle
