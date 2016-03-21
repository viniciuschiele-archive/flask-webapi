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
    elif isinstance(message, dict):
        for key, value in message.items():
            message[key] = format_error_message(value, **kwargs)
    return message
