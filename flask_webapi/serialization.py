import copy
import inspect

from flask import request, current_app
from .filters import action_filter


class serializer(action_filter):
    """
    A decorator that apply a serializer to the action.
    :param Schema schema: The schema used to serialize the data.
    :param bool many: If set to `True` the object will be serialized to a list.
    :param str envelope: The key used to envelope the data.
    :return: A function.
    """
    def __init__(self, schema, many=None, envelope=None,  order=-1):
        super().__init__(order)

        self.schema = schema() if inspect.isclass(schema) else schema
        self.many = many
        self.envelope = envelope

    def before_action(self, context):
        pass

    def after_action(self, context):
        result = context.result

        if result is None:
            return

        if result is current_app.response_class:
            return

        schema = self.schema
        many = self.many

        # Gets the field names from the query string,
        # only those fields are going to be dumped.
        fields = request.args.get('fields')

        if fields:
            # schema has to be cloned to avoid
            # problem with multiple threads.
            schema = copy.copy(schema)
            schema.only = fields.split(',')
            schema.refresh()

        if many is None:
            many = isinstance(result, (list, tuple))

        if many:
            result = schema.dumps(result)
        else:
            result = schema.dump(result)

        if self.envelope:
            result = {self.envelope: result}

        context.result = result


