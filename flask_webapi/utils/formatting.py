"""
This module contains functions to deal with error messages.
"""


def prepare_error_message_for_response(errors, message, field=None):
    """
    Formats the given message in a specific format.
    :param errors: The output list of errors.
    :param message: The error message.
    :param field: The current field.
    Examples::
            [
                {message='error 1', field='field 1'}
                {message='error 2', field='field 2'},
            ]
    """
    if isinstance(message, dict):
        for f, m in message.items():
            prepare_error_message_for_response(errors, m, f)
    elif isinstance(message, list):
        for message in message:
            if isinstance(message, str):
                data = {'message': message}
                if field is not None:
                    data['field'] = field
                errors.append(data)
            else:
                if field is not None:
                    message['field'] = field
                errors.append(message)
