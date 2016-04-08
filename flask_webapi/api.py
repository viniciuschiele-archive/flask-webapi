"""
Provides the main class for Flask WebAPI.
"""

import importlib
import inspect

from .actions import ActionContext, ActionDescriptorBuilder, DefaultActionExecutor
from .formatters import get_default_input_formatters, get_default_output_formatters
from .negotiators import DefaultContentNegotiator
from .parameters import get_default_providers
from .routers import has_routes, DefaultRouter
from .views import exception_handler


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
        self.action_executor = DefaultActionExecutor()
        self.content_negotiator = DefaultContentNegotiator()
        self.filters = []
        self.input_formatters = get_default_input_formatters()
        self.output_formatters = get_default_output_formatters()
        self.exception_handler = exception_handler
        self.router = DefaultRouter()
        self.value_providers = get_default_providers()

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
            view = type('FunctionBasedView', (object,), {view.__name__: view})

        if not inspect.isclass(view):
            raise TypeError('View must be a class')

        routes = self.router.get_routes(view)

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
                if inspect.isfunction(member) and has_routes(member):
                    self.add_view(member)
                elif inspect.isclass(member) and member.__name__.endswith('View'):
                    self.add_view(member)

    def _make_view(self, descriptor):
        """
        Returns a view function expected by Flask.
        :param ActionDescriptor descriptor: The action descriptor.
        :return: A function
        """
        def func_view(*args, **kwargs):
            context = ActionContext(descriptor, self, args, kwargs)
            self.action_executor.execute(context)
            return context.response
        return func_view

    def _register_routes(self, routes):
        """
        Registers a list of routes into Flask.
        :param routes: The list of routes.
        """
        builder = ActionDescriptorBuilder()
        for route in routes:
            descriptor = builder.build(route.func, route.view_class, self)
            self.app.add_url_rule(route.url, route.endpoint, self._make_view(descriptor), methods=route.methods)
