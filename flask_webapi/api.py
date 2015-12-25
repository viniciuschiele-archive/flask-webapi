import inspect

from werkzeug.utils import import_string
from .negotiation import DefaultContentNegotiator
from .renderers import JSONRenderer
from .views import APIView


class WebAPI(object):
    def __init__(self, app=None):
        self.app = None
        self.authenticators = []
        self.permissions = []
        self.content_negotiator = DefaultContentNegotiator
        self.parsers = []
        self.renderers = [JSONRenderer]

        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app

    def load_module(self, module_name):
        module = import_string(module_name)

        members = inspect.getmembers(module, predicate=lambda obj: inspect.isclass(obj) and issubclass(obj, APIView) and obj != APIView)

        for name, cls in members:
            cls.register(self)
