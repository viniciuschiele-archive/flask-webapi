from flask import request
from .negotiation import perform_content_negotiation
from .utils import unpack


def make_response(data):
    """
    Creates a Flask response object from the specified data.
    The appropriated encoder is taken based on the request header Accept.
    If there is not data to be serialized the response status code is 204.

    :param data: The Python object to be serialized.
    :return: A Flask response object.
    """

    response_class = request.action.app.response_class

    status = headers = None
    if isinstance(data, tuple):
        data, status, headers = unpack(data)

    if data is None:
        data = response_class(status=204)
    elif not isinstance(data, response_class):
        if not hasattr(request, 'accepted_renderer'):
            perform_content_negotiation(force=True)

        data_bytes = request.accepted_renderer.render(data, request.accepted_mimetype)
        data = response_class(data_bytes, mimetype=request.accepted_mimetype.mimetype)

    if status is not None:
        data.status_code = status

    if headers:
        data.headers.extend(headers)

    return data

