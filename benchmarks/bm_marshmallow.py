import random
import string
import time

from flask_webapi import serializers
from marshmallow import fields, Schema


def generate_random_string(size):
    return ''.join(random.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(size))


class Model(object):
    property1 = None
    property2 = generate_random_string(20)
    property3 = generate_random_string(30)
    property4 = generate_random_string(40)
    property5 = generate_random_string(50)
    property6 = generate_random_string(60)
    property7 = generate_random_string(70)
    property8 = generate_random_string(80)
    property9 = generate_random_string(90)
    property10 = generate_random_string(100)
    property11 = generate_random_string(110)
    property12 = generate_random_string(120)
    property13 = generate_random_string(130)
    property14 = generate_random_string(140)
    property15 = 123456789


class ModelSerializer(serializers.Serializer):
    property1 = serializers.StringField(allow_none=True)
    property2 = serializers.StringField()
    property3 = serializers.StringField()
    property4 = serializers.StringField()
    property5 = serializers.StringField()
    property6 = serializers.StringField()
    property7 = serializers.StringField()
    property8 = serializers.StringField()
    property9 = serializers.StringField()
    property10 = serializers.StringField()
    property11 = serializers.StringField()
    property12 = serializers.StringField()
    property13 = serializers.StringField()
    property14 = serializers.StringField()
    property15 = serializers.IntegerField()


class ModelSchema(Schema):
    property1 = fields.String(allow_none=True)
    property2 = fields.String()
    property3 = fields.String()
    property4 = fields.String()
    property5 = fields.String()
    property6 = fields.String()
    property7 = fields.String()
    property8 = fields.String()
    property9 = fields.String()
    property10 = fields.String()
    property11 = fields.String()
    property12 = fields.String()
    property13 = fields.String()
    property14 = fields.String()
    property15 = fields.Integer()


if __name__ == '__main__':
    model = Model()

    serializer = ModelSerializer()
    schema = ModelSchema()

    s = time.time()
    for i in range(500):
        data = ModelSerializer().dump(model)
    print('Serializer - dump: ' + str(time.time() - s))

    s = time.time()
    for i in range(500):
        data2 = schema.dump(model).data
    print('Marshmallow - dump: ' + str(time.time() - s))

    models = [Model() for i in range(500)]

    serializer = ModelSerializer(many=True)
    schema = ModelSchema(many=True)

    s = time.time()
    data = serializer.dump(models)
    print('Serializer - dump: ' + str(time.time() - s))

    s = time.time()
    data2 = schema.dump(models).data
    print('Marshmallow - dump: ' + str(time.time() - s))

    s = time.time()
    serializer.load(data)
    print('Serializer - load: ' + str(time.time() - s))

    s = time.time()
    d = schema.load(data2)
    print('Marshmallow - load: ' + str(time.time() - s))
