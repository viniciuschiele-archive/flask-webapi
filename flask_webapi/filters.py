"""
Provides filters used to inject code into views.
"""


def authentication_filter(function):
    """
    Filter that performs authentication.
    :param function: The authentication function.
    """
    def inner(*args, **kwargs):
        def inner2(f):
            order = kwargs.pop('order', -1)
            authenticate = function(*args, **kwargs)

            def outer(f):
                def outer2(*args, **kwargs):
                    authenticate()
                    return f(*args, **kwargs)
                return outer2

            f.filters = getattr(f, 'filters', [])
            f.filters.append((authentication_filter, outer, order))
            return f
        return inner2
    return inner


def authorization_filter(function):
    """
    Filter that performs authorization.
    :param function: The authorization function.
    """
    def inner(*args, **kwargs):
        def inner2(f):
            order = kwargs.pop('order', -1)
            authorize = function(*args, **kwargs)

            def outer(f):
                def outer2(*args, **kwargs):
                    authorize()
                    return f(*args, **kwargs)
                return outer2

            f.filters = getattr(f, 'filters', [])
            f.filters.append((authorization_filter, outer, order))
            return f
        return inner2
    return inner


def action_filter(function):
    """
    Filter that performs authorization.
    :param function: The authorization function.
    """
    def inner(*args, **kwargs):
        def inner2(f):
            order = kwargs.pop('order', -1)
            action = function(*args, **kwargs)

            def outer(f):
                def outer2(*args, **kwargs):
                    return action(f, *args, **kwargs)
                return outer2

            f.filters = getattr(f, 'filters', [])
            f.filters.append((authorization_filter, outer, order))
            return f
        return inner2
    return inner


def exception_filter(function):
    """
    Filter that performs authorization.
    :param function: The authorization function.
    """
    def inner(*args, **kwargs):
        def inner2(f):
            order = kwargs.pop('order', -1)
            handle_error = function(*args, **kwargs)

            def outer(f):
                def outer2(*args, **kwargs):
                    try:
                        return f(*args, **kwargs)
                    except Exception as e:
                        return handle_error(e)
                return outer2

            f.filters = getattr(f, 'filters', [])
            f.filters.append((exception_filter, outer, order))
            return f
        return inner2
    return inner
