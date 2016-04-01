"""
Provides filters used to inject code into views.
"""


def filter(filter_cls):
    """
    Filter that performs authentication.
    :param filter_cls:
    """
    return filter_cls


@filter
class authentication_filter(object):
    """
    Filter that performs authentication.
    """
    def __init__(self, order=-1):
        self.order = order

    def __call__(self, func):
        func.filters = getattr(func, 'filters', [])
        func.filters.append(self)
        return func

    def authenticate(self, context):
        pass


@filter
class authorization_filter(object):
    """
    Filter that performs authorization.
    """
    def __init__(self, order=-1):
        self.order = order

    def __call__(self, func):
        func.filters = getattr(func, 'filters', [])
        func.filters.append(self)
        return func

    def authorize(self, context):
        pass


@filter
class action_filter(object):
    """
    Filter that performs authorization.
    """
    def __init__(self, order=-1):
        self.order = order

    def __call__(self, func):
        func.filters = getattr(func, 'filters', [])
        func.filters.append(self)
        return func

    def before_action(self, context):
        pass

    def after_action(self, context):
        pass


@filter
class response_filter(object):
    """
    Filter that performs authorization.
    """
    def __init__(self, order=-1):
        self.order = order

    def __call__(self, func):
        func.filters = getattr(func, 'filters', [])
        func.filters.append(self)
        return func

    def before_response(self, context):
        pass

    def after_response(self, context):
        pass


@filter
class exception_filter(object):
    """
    Filter that performs authorization.
    """
    def __init__(self, order=-1):
        self.order = order

    def __call__(self, func):
        func.filters = getattr(func, 'filters', [])
        func.filters.append(self)
        return func

    def handle_exception(self, context):
        pass

