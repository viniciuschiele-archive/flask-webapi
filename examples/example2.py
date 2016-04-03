from flask import Flask
from flask_webapi import WebAPI, View, route, param, serialize
from flask_webapi.exceptions import NotFound, ValidationError
from flask_webapi.serialization import Schema, StringField, IntegerField


class User(object):
    def __init__(self, username=None, password=None, first_name=None, last_name=None, age=None):
        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.age = age


class UserSchema(Schema):
    username = StringField()
    password = StringField(load_only=True)
    first_name = StringField()
    last_name = StringField()
    age = IntegerField(required=False)

    def post_load(self, data, original_data):
        return User(**data)


users = [
    User(username='john.smith', password='1234', first_name='John', last_name='Smith', age=30)
]


@route('/users')
@serialize(UserSchema)
class UserView(View):
    @route('/', methods=['POST'])
    @param('user', UserSchema())
    def add_user(self, user):
        if any([db_user for db_user in users if db_user.username == user.username]):
            raise ValidationError('User already exists: ' + user.username)

        users.append(user)
        return user

    @route('/<username>', methods=['DELETE'])
    def delete_user(self, username):
        found = [user for user in users if user.username == username]

        if not found:
            raise NotFound('User not found: ' + username)

        users.remove(found[0])

    @route('/')
    @param('username', StringField(default=None))
    def get_users(self, username):
        if username:
            return [user for user in users if username in user.username]
        return users

    @route('/<username>')
    def get_user(self, username):
        for user in users:
            if username == user.username:
                return user

        raise NotFound('User not found: ' + username)


if __name__ == '__main__':
    app = Flask(__name__)
    api = WebAPI(app)
    api.add_view(UserView)
    app.run()
