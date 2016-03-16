"""
Provides the main class for Flask WebAPI.
"""

import inspect

from werkzeug.utils import import_string
from .authorization import AllowAny
from .negotiation import DefaultContentNegotiator
from .parsers import build_locations, JSONParser
from .renderers import JSONRenderer
from .utils.routing import Route
from .views import ViewBase, ViewContext


class WebAPI(object):
    """
    The main entry point for the application.
    You need to initialize it with a Flask Application: ::

    >>> app = Flask(__name__)
    >>> api = WebAPI(app)

    Alternatively, you can use :meth:`init_app` to set the Flask application
    after it has been constructed.
    """

    def __init__(self, app=None):
        """
        Initialize this class with the given :class:`flask.Flask` application
        :param app: the Flask application
        :type app: flask.Flask
        Examples::
            api = WebAPI()
            api.add_view(...)
            api.init_app(app)
        """
        self._routes = []

        self.app = None
        self.authenticators = []
        self.permissions = [AllowAny()]
        self.content_negotiator = DefaultContentNegotiator()
        self.parsers = [JSONParser()]
        self.renderers = [JSONRenderer()]
        self.exception_handler = None
        self.parser_locations = build_locations()

        if app:
            self.init_app(app)

    def add_view(self, view):
        """
        Adds a view to the WebAPI.
        :param view: the class of your view
        """
        if inspect.isclass(view):
            if not issubclass(view, ViewBase):
                raise TypeError('View must inherit from %s.' % ViewBase.__name__)
        elif inspect.isfunction(view):
            if not hasattr(view, 'routes'):
                raise TypeError('View has not routes.')
            view = type('WrappedViewBase', (ViewBase,), {view.__name__: view})
        else:
            raise TypeError('Invalid view type.')

        routes = self._get_routes(view)

        if self.app:
            self._register_routes(routes)
        else:
            self._routes.extend(routes)

    def scan(self, module):
        """
        Tries to import modules and register its views.
        :param module: The path of the module or the module itself.
        """
        if type(module) is str:
            module = import_string(module)

        members = inspect.getmembers(module)

        for _, member in members:
            if inspect.isfunction(member) and hasattr(member, 'routes'):
                self.add_view(member)
            elif inspect.isclass(member) and issubclass(member, ViewBase):
                self.add_view(member)

    def init_app(self, app):
        """
        Initialize this class with the given :class:`flask.Flask` application
        :param app: the Flask application
        :type app: flask.Flask
        Examples::
            api = WebAPI()
            api.add_view(...)
            api.init_app(app)
        """
        self.app = app

        # gets all the module paths from the config
        # and import them to register its views.
        modules = self.app.config.get('WEBAPI_IMPORTS')
        if modules:
            for module in modules:
                self.scan(module)

        # register all views added before the initialization
        if self._routes:
            self._register_routes(self._routes)

    def _get_routes(self, view):
        view_routes = getattr(view, 'routes', [])
        if len(view_routes) == 0:
            view_routes.append(('', None, None))

        routes = []

        for method_name in dir(view):
            func = getattr(view, method_name)
            func_routes = getattr(func, 'routes', None)

            if not func_routes:
                continue

            for prefix, _, _ in view_routes:
                for url, endpoint, methods in func_routes:
                    if not endpoint:
                        endpoint = self._make_endpoint(view, func)
                    routes.append(Route(prefix + url, endpoint, methods, func, view))

        return routes

    def _make_endpoint(self, view, func):
        """
        Returns a endpoint for the specified view and func.
        :param ViewBase view: The class of your view
        :param func: The function of your view
        :return: The endpoint
        """
        return view.__name__ + ':' + func.__name__

    def _make_view(self, context):
        """
        Returns a view method expected by Flask.
        :param ViewContext context: The view context
        :return: A function
        """
        def view(*args, **kwargs):
            instance = context.view()
            instance.context = context
            return instance.dispatch(*args, **kwargs)
        return view

    def _register_routes(self, routes):
        """
        Registers a list of routes into Flask.
        :param routes: The list of routes.
        """
        for route in routes:
            context = ViewContext(route.func, route.view, self)
            self.app.add_url_rule(route.url, route.endpoint, self._make_view(context), methods=route.methods)
