"""
Provides filters used to inject code into methods.
"""


def action_filter(function):
    """
    Filter used to inject code before and after the execution of the action.
    :param function: The function to be injected.
    """
    def wrapper(*args, **kwargs):
        def execute(f):
            order = kwargs.pop('order', -1)
            next = function(*args, **kwargs)

            f.filters = getattr(f, 'filters', [])
            f.filters.append((action_filter, next, order))
            return f
        return execute
    return wrapper


def exception_filter(function):
    """
    Filter used to inject code when an exception is raised.
    :param function: The function to be injected.
    """
    def wrapper(*args, **kwargs):
        def execute(f):
            order = kwargs.pop('order', -1)
            next = function(*args, **kwargs)

            f.filters = getattr(f, 'filters', [])
            f.filters.append((action_filter, next, order))
            return f
        return execute
    return wrapper
