import time

from flask import Flask, Response
from flask_webapi import WebAPI, route


def flask_request():
    return Response()


@route('/webapi_request')
def webapi_request():
    return Response()


if __name__ == '__main__':
    app = Flask(__name__)
    app.add_url_rule('/flask_request', view_func=flask_request)

    api = WebAPI(app)
    api.add_view(webapi_request)

    client = app.test_client()

    # warm up
    client.get('/flask_request')
    client.get('/webapi_request')

    s = time.time()

    for i in range(1000):
        client.get('/flask_request')

    print('Flask: ' + str(time.time() - s))

    s = time.time()

    for i in range(1000):
        client.get('/webapi_request')

    print('WebAPI: ' + str(time.time() - s))
