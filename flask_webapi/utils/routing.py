def get_view_prefixes(view):
    return [prefix for prefix, _, _ in getattr(view, 'routes', [])]


def get_view_routes(view):
    return getattr(view, 'routes', None)


def urljoin(*urls):
    return '/' + '/'.join([url.strip('/') for url in urls])


class Route(object):
    def __init__(self, url, endpoint, methods, func, view):
        self.url = url
        self.endpoint = endpoint
        self.methods = methods
        self.func = func
        self.view = view
