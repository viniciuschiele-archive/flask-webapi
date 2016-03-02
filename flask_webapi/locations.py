from flask import request


def load_query():
    return request.args


def guess_location(field):
    location = getattr(field, 'location', None)
    if location is None:
        location = 'query' if request.method == 'GET' else 'body'
    return location
