from flask import Flask
from flask_webapi import WebAPI
from flask_webapi.exceptions import NotFound
from flask_webapi.decorators import route, param, serializer
from flask_webapi.serializers import Serializer, StringField, IntegerField


class User(object):
    def __init__(self, username=None, first_name=None, last_name=None, age=None):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.age = age


class UserSerializer(Serializer):
    username = StringField()
    first_name = StringField()
    last_name = StringField()
    age = IntegerField()


users = [User(username='john.smith', first_name='John', last_name='Smith', age=30)]


@route('/users')
@param('username', StringField(default=None))
@serializer(UserSerializer, many=True)
def get_users(username):
    if username:
        return [user for user in users if username in user.username]
    return users


@route('/users/<username>')
@serializer(UserSerializer)
def get_user(username):
    for user in users:
        if username == user.username:
            return user

    return NotFound()

if __name__ == '__main__':
    app = Flask(__name__)
    api = WebAPI(app)
    api.add_view(get_user)
    api.add_view(get_users)
    app.run()
