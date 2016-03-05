class Route(object):
    def __init__(self, url, endpoint, methods, func, view):
        self.url = url
        self.endpoint = endpoint
        self.methods = methods
        self.func = func
        self.view = view
