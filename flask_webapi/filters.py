"""
Provides a set of filter classes used to inject code into actions.
"""

import inspect

from flask import request
from .exceptions import ValidationError, UnsupportedMediaType
from .fields import Schema
from .results import BadRequestResult, ForbiddenResult, UnauthorizedResult, UnsupportedMediaTypeResult


class Filter:
    """
    A base class from which all filter classes should inherit.
    :param order: The order in which the filter is executed.
    """

    # `True` to allow multiple filters of the same type
    # on the same action.
    # `False` to use only the last filter.
    allow_multiple = True

    def __init__(self, order=-1):
        self.order = order

    def __call__(self, action_or_view):
        """
        Applies the filter on the given action.
        :param action_or_view: The action or view that will receive the filter.
        """
        action_or_view.filters = getattr(action_or_view, 'filters', [])
        action_or_view.filters.append(self)
        return action_or_view


class AuthenticationFilter(Filter):
    """
    A filter that surrounds execution of the authentication.
    """
    def on_authentication(self, context):
        """
        Called early in the filter pipeline to confirm request is authenticated.
        :param ActionContext context: The action context.
        """
        pass


class AuthorizationFilter(Filter):
    """
    A filter that surrounds execution of the authorization.
    """
    def on_authorization(self, context):
        """
        Called early in the filter pipeline to confirm request is authorized.
        :param ActionContext context: The action context.
        """
        pass


class ResourceFilter(Filter):
    """
    A filter that surrounds execution of the action (and filters) and the response (and filters).
    """
    def on_resource_execution(self, context, next_filter):
        """
        Called before execution of the remainder of the pipeline.
        :param ActionContext context: The action context.
        :param next_filter: The next filter to be called.
        """
        pass


class ExceptionFilter(Filter):
    """
    A filter that runs after an action has thrown an `Exception`.
    """
    def on_exception(self, context):
        """
        Called after an action has thrown an `Exception`.
        :param ActionContext context: The action context.
        """
        pass


class ActionFilter(Filter):
    """
    A filter that surrounds execution of the action.
    """
    def on_action_execution(self, context, next_filter):
        """
        Called before the action executes.
        :param ActionContext context: The action context.
        :param next_filter: The next filter to be called.
        """
        pass


class ResultFilter(Filter):
    """
    A filter that surrounds creation of the response.
    """

    def on_result_execution(self, context, next_filter):
        """
        Called before the response creation.
        :param ActionContext context: The action context.
        :param next_filter: The next filter to be called.
        """
        pass


####################################################
# Below are the implementation of the above filters.
####################################################


class AllowAnonymous(Filter):
    """
    A filter that allows anonymous requests, disabling some `AuthorizationFilter`.
    """

    allow_multiple = False


class AuthenticateFilter(AuthenticationFilter):
    """
    Specifies the authenticator that validates the credentials for the current user.

    :param list authenticators: The list of `Authenticator`.
    :param int order: The order in which the filter is executed.
    """
    def __init__(self, *authenticators, order=-1):
        super().__init__(order)
        self.authenticators = [item() if inspect.isclass(item) else item for item in authenticators]

    def on_authentication(self, context):
        """
        Authenticates the current user.
        :param ActionContext context: The action context.
        """
        request.user = None
        request.auth = None

        for authenticator in self.authenticators:
            result = authenticator.authenticate()

            if result.succeeded:
                request.user = result.user
                request.auth = result.auth
                break

            if result.failure:
                context.result = UnauthorizedResult(result.failure)
                break


class AuthorizeFilter(AuthorizationFilter):
    """
    Specifies that access to a view or action method is
    restricted to users who meet the authorization requirement.

    :param list permissions: The list of `Permission`.
    :param int order: The order in which the filter is executed.
    """
    def __init__(self, *permissions, order=-1):
        super().__init__(order)
        self.permissions = [permission() if inspect.isclass(permission) else permission for permission in permissions]

    def on_authorization(self, context):
        """
        Authorize the current user.
        :param ActionContext context: The action context.
        """
        # if there is an `AllowAnonymous` filter
        # we don't apply authorization.
        if [f for f in context.filters if isinstance(f, AllowAnonymous)]:
            return

        for permission in self.permissions:
            if permission.has_permission():
                return

        if getattr(request, 'user', None):
            context.result = ForbiddenResult('You do not have permission to perform this action.')
        else:
            context.result = UnauthorizedResult('Authentication credentials were not provided.')


class CompatFilter(ResourceFilter):
    """
    A filter that apply a decorator built for Flask.

    >>> from flask.ext.cache import Cache
    >>> cache = Cache(...)

    >>> @route('/users')
    >>> @compat(cache.cached())
    >>> def get_users():

    :param decorator: The decorator.
    :param int order: The order in which the filter is executed.
    """

    def __init__(self, decorator, order=-1):
        super().__init__(order)
        self.decorator = decorator(self._next_filter)

    def on_resource_execution(self, context, next_filter):
        request.compat_filter = (context, next_filter)

        self.decorator(*context.args, **context.kwargs)

    def _next_filter(self, *args, **kwargs):
        context, next_filter = request.compat_filter

        del request.compat_filter

        context.args = args
        context.kwargs = kwargs

        next_filter(context)

        return context.response


class ConsumeFilter(ResourceFilter):
    """
    A filter that specifies the supported request content types
    :param content_type: The content type.
    :param int order: The order in which the filter is executed.
    """

    allow_multiple = False

    def __init__(self, content_type, order=-1):
        super().__init__(order)
        self.content_type = content_type

    def on_resource_execution(self, context, next_filter):
        request.environ['CONTENT_TYPE'] = self.content_type
        next_filter(context)


class ProduceFilter(ResultFilter):
    """
    A filter that specifies the supported response content types.
    :param content_types: The list of content types.
    :param int order: The order in which the filter is executed.
    """

    allow_multiple = False

    def __init__(self, *content_types, order=-1):
        super().__init__(order)
        self.content_type = ';'.join(content_types)

    def on_result_execution(self, context, next_filter):
        request.environ['HTTP_ACCEPT'] = self.content_type
        next_filter(context)


class ParameterFilter(ActionFilter):
    """
    Filter that retrieve a specific parameter from a specific location.
    :param str name: The name of parameter.
    :param Field field: The field used to parse the argument.
    :param str location: The location from where to retrieve the value.
    """
    def __init__(self, name, field, location=None, order=-1):
        super().__init__(order)

        if isinstance(field, type):
            field = field()

        self.is_schema = isinstance(field, Schema)

        if not self.is_schema:
            field = type('ParamSchema', (Schema,), {name: field})()

        self.name = name
        self.field = field
        self.location = location

    def on_action_execution(self, context, next_filter):
        try:
            data = self._get_arguments(context)
        except UnsupportedMediaType as e:
            context.result = UnsupportedMediaTypeResult(e.message)
        except ValueError as e:
            context.result = BadRequestResult(str(e))
        else:
            try:
                result = self.field.load(data)

                if self.is_schema:
                    context.kwargs[self.name] = result
                else:
                    context.kwargs.update(result)
            except ValidationError as e:
                errors = {}
                errors.update(e.message)

                if errors:
                    raise ValidationError(errors)

        next_filter(context)

    def _get_arguments(self, context):
        """
        Gets the argument data based on the location.
        :return: The data obtained.
        """
        if not self.location:
            location = 'query' if request.method == 'GET' else 'body'
        else:
            location = self.location

        provider = context.value_providers.get(location)

        if provider is None:
            raise Exception('Value provider for location "%s" not found.' % location)

        return provider.get_data(context)


class ObjectResultFilter(Filter):
    allow_multiple = False

    def __init__(self, schema, status_code=None):
        super().__init__()

        self.schema = schema() if inspect.isclass(schema) else schema
        self.status_code = status_code
