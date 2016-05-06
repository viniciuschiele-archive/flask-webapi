from abc import ABCMeta, abstractmethod
from . import status


class ActionResult(metaclass=ABCMeta):
    @abstractmethod
    def execute(self, context):
        pass


class StatusCodeResult(ActionResult):
    def __init__(self, status_code):
        self.status_code = status_code

    def execute(self, context):
        context.response.status_code = self.status_code


class NoContent(StatusCodeResult):
    def __init__(self):
        super().__init__(status.HTTP_204_NO_CONTENT)


class ObjectResult(ActionResult):
    def __init__(self, value, schema=None, status_code=None):
        self.value = value
        self.schema = schema
        self.status_code = status_code

    def execute(self, context):
        executor = context.object_result_executor
        executor.execute(context, self)


class CreatedResult(ObjectResult):
    def __init__(self, value=None, schema=None):
        super().__init__(value, schema=schema, status_code=status.HTTP_201_CREATED)


class BadRequestResult(ObjectResult):
    def __init__(self, value=None, schema=None):
        super().__init__(value, schema=schema, status_code=status.HTTP_400_BAD_REQUEST)


class NotFoundResult(ObjectResult):
    def __init__(self, value=None, schema=None):
        super().__init__(value, schema=schema, status_code=status.HTTP_404_NOT_FOUND)


class UnauthorizedResult(ObjectResult):
    def __init__(self, value=None, schema=None):
        super().__init__(value, schema=schema, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenResult(ObjectResult):
    def __init__(self, value=None, schema=None):
        super().__init__(value, schema=schema, status_code=status.HTTP_403_FORBIDDEN)


class UnsupportedMediaTypeResult(ObjectResult):
    def __init__(self, value=None, schema=None):
        super().__init__(value, schema=schema, status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
