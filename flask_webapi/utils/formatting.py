"""
This module contains functions to deal with error messages.
"""


def format_error_message(message, **kwargs):
    """
    Replaces the tokens by `kwargs`.

    :param message: The message that contains the tokens.
    :param kwargs: The args used to replace the tokens.
    :return: The message formatted.
    """
    if isinstance(message, str):
        message = message.format(**kwargs)
    elif message is dict:
        for key, value in message.items():
            message[key] = format_error_message(value, **kwargs)
    return message


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
            prepare_error_message_for_response(errors, message, field)
    else:
        if hasattr(message, 'message'):  # is a ValidatorError
            data = {'message': message.message}
            data.update(message.kwargs)
        else:
            data = {'message': str(message)}

        if field:
            data['field'] = field

        errors.append(data)
