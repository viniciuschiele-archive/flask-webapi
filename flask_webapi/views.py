class ViewBase(object):
    pass


class ViewAction(object):
    def __init__(self):
        self.func = None
        self.authenticators = []
        self.permissions = []
        self.content_negotiator = None
        self.parsers = []
        self.renderers = []
        self.serializer = None
        self.envelope = None

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def get_authenticators(self):
        """
        Instantiates and returns the list of authenticators that this view can use.
        """
        return [authenticator() for authenticator in self.authenticators]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        return [permission() for permission in self.permissions]

    def get_content_negotiator(self):
        """
        Instantiates and returns the content negotiator that this action can use.
        """
        return self.content_negotiator()

    def get_parsers(self):
        """
        Instantiates and returns the list of parsers that this view can use.
        """
        return [parser() for parser in self.parsers]

    def get_renderers(self):
        """
        Instantiates and returns the list of renderers that this view can use.
        """
        return [renderer() for renderer in self.renderers]

    def get_serializer(self, fields=()):
        """
        Instantiates and returns the serializer that this action can use.

        :param fields: The name of the fields to be serialized.
        """
        return self.serializer(only=fields)
