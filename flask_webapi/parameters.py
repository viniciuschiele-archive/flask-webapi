from flask import request


def build_locations():
    return {
        'header': lambda context: request.headers,
        'query': lambda context: request.args,
        'body': parse_body
    }


def guess_location(field):
    location = getattr(field, 'location', None)
    if location is None:
        location = 'query' if request.method == 'GET' else 'body'
    return location


def parse_body(context):
    if request.content_type == 'application/x-www-form-urlencoded':
        return request.form

    negotiator = context.get_content_negotiator()
    parsers = context.get_parsers()

    parser_pair = negotiator.select_parser(parsers)

    if not parser_pair:
        raise Exception()

    parser, mimetype = parser_pair

    return parser.parse(request.data, mimetype)
