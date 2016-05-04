import inspect

from collections import Iterable, Mapping


def is_generator(obj):
    """
    Return True if ``obj`` is a generator
    """
    return inspect.isgeneratorfunction(obj) or inspect.isgenerator(obj)


def is_iterable_but_not_string(obj):
    """
    Return True if ``obj`` is an iterable object that isn't a string.
    """
    return (isinstance(obj, Iterable) and not hasattr(obj, "strip")) or is_generator(obj)


def is_collection(obj):
    """
    Return True if ``obj`` is a collection type, e.g list, tuple, queryset.
    """
    return is_iterable_but_not_string(obj) and not isinstance(obj, Mapping)
