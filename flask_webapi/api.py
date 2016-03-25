"""
Provides the main class for Flask WebAPI.
"""

import importlib
import inspect

from flask import request
from .negotiators import DefaultContentNegotiator
from .parameters import get_argument_providers
from .parsers import JSONParser, FormDataParser
from .permissions import AllowAny
from .renderers import JSONRenderer
from .utils.routing import Route, urljoin, get_view_prefixes, get_view_routes
from .views import exception_handler, BaseView, View, Action


class WebAPI(object):
    """
    The main entry point for the application.
    You need to initialize it with a Flask Application: ::

    >>> app = Flask(__name__)
    >>> api = WebAPI(app)

    Alternatively, you can use `init_app` to set the Flask application
    after it has been constructed.
    """

    def __init__(self, app=None):
        """
        Initialize this class with the given `flask.Flask` application.
        :param flask.Flask app: The Flask application
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
        self.parsers = [JSONParser(), FormDataParser()]
        self.renderers = [JSONRenderer()]
        self.exception_handler = exception_handler
        self.argument_providers = get_argument_providers()

        if app:
            self.init_app(app)

    def init_app(self, app):
        """
        Initializes this class with the given :class:`flask.Flask` application
        :param app: the Flask application
        :type app: flask.Flask
        Examples::
            api = WebAPI()
            api.add_view(...)
            api.init_app(app)
        """
        self.app = app

        # register all views added before the initialization
        if self._routes:
            self._register_routes(self._routes)

    def add_view(self, view):
        """
        Adds a view to the WebAPI.
        The view can be either a function or a class.
        :param view: The function or class of your view.
        """
        if inspect.isfunction(view):
            view = type('FunctionBasedView', (View,), {view.__name__: view})

        if not inspect.isclass(view) or not issubclass(view, BaseView):
            raise TypeError('View must be a class and must inherit from %s.' % BaseView.__name__)

        routes = self._build_routes(view)

        # If Flask app was set, it adds
        # the view straightway to the Flask app
        # otherwise it adds the view into an array
        # to be used in `init_app`.
        if self.app:
            self._register_routes(routes)
        else:
            self._routes.extend(routes)

    def scan_views(self, packages, module_name='views'):
        """
        Scans the given packages looking for views.
        :param str|list packages: The list of package names.
        :param str module_name: The name of the module which contains the views.
        """
        if not isinstance(packages, (list, tuple)):
            packages = [packages]

        for package in packages:
            module = importlib.import_module(package + '.' + module_name)

            # Go through all members to check which one is an action.
            members = inspect.getmembers(module)

            for _, member in members:
                if inspect.isfunction(member) and hasattr(member, 'routes'):
                    self.add_view(member)
                elif inspect.isclass(member) and issubclass(member, BaseView):
                    self.add_view(member)

    def _make_endpoint(self, view, func):
        """
        Returns an endpoint for the given view and func.
        :param BaseView view: The class of your view.
        :param func: The function of your view.
        :return str: The endpoint as string.
        """
        return func.__module__ + '.' + view.__name__ + '.' + func.__name__

    def _make_view(self, action):
        """
        Returns a view function expected by Flask.
        :param Action action: The action.
        :return: A function
        """
        def view(*args, **kwargs):
            request.action = action
            instance = action.view()
            return instance.dispatch(*args, **kwargs)
        return view

    def _build_routes(self, view):
        """
        Returns the routes for the given view.
        :param view: The view.
        :return: A list of routes.
        """
        ret = []

        # routes can be set using the decorator
        # @route on top of the class view.
        # e.g:
        #
        # @route('/prefix')
        # class MyView(BaseView):
        prefixes = get_view_prefixes(view) or [None]

        for _, func in inspect.getmembers(view):
            routes = get_view_routes(func)

            # if the action hasn't routes
            # it is ignored.
            if not routes:
                continue

            for url, endpoint, methods in routes:
                for prefix in prefixes:
                    if prefix:
                        url = urljoin(prefix, url)

                    if not endpoint:
                        endpoint = self._make_endpoint(view, func)

                    ret.append(Route(url, endpoint, methods, func, view))

        return ret

    def _register_routes(self, routes):
        """
        Registers a list of routes into Flask.
        :param routes: The list of routes.
        """
        for route in routes:
            action = Action(route.func, route.view, self)
            self.app.add_url_rule(route.url, route.endpoint, self._make_view(action), methods=route.methods)
