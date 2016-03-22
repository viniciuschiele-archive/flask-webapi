"""
Provides helper functions to deal with inspection and reflection.
"""

import inspect


def has_self_argument(func):
    """
    Checks whether the given func has a self argument.
    :param func: The func to be checked.
    :return: True if the func has the self argument.
    """
    func_args = inspect.getargspec(func).args
    return len(func_args) > 0 and func_args[0] == 'self'


def func_to_method(func):
    """
    Converts a function to a method.
    A function does not have a self argument while
    a method has it.
    :param func: The function to be converted.
    :return: A method.
    """
    def handle(_, *args, **kwargs):
        return func(*args, **kwargs)
    return handle
