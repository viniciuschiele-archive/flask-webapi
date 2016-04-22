import random
import string
import time

from flask_webapi import fields
from marshmallow import fields as mm_fields, Schema


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


class ModelSchema(fields.Schema):
    property1 = fields.StringField(allow_none=True)
    property2 = fields.StringField()
    property3 = fields.StringField()
    property4 = fields.StringField()
    property5 = fields.StringField()
    property6 = fields.StringField()
    property7 = fields.StringField()
    property8 = fields.StringField()
    property9 = fields.StringField()
    property10 = fields.StringField()
    property11 = fields.StringField()
    property12 = fields.StringField()
    property13 = fields.StringField()
    property14 = fields.StringField()
    property15 = fields.IntegerField()


class MM_ModelSchema(Schema):
    property1 = mm_fields.String(allow_none=True)
    property2 = mm_fields.String()
    property3 = mm_fields.String()
    property4 = mm_fields.String()
    property5 = mm_fields.String()
    property6 = mm_fields.String()
    property7 = mm_fields.String()
    property8 = mm_fields.String()
    property9 = mm_fields.String()
    property10 = mm_fields.String()
    property11 = mm_fields.String()
    property12 = mm_fields.String()
    property13 = mm_fields.String()
    property14 = mm_fields.String()
    property15 = mm_fields.Integer()


if __name__ == '__main__':
    # model = Model()
    #
    # serializer = ModelSerializer()
    # schema = ModelSchema()
    #
    # s = time.time()
    # for i in range(500):
    #     data = ModelSerializer().dump(model)
    # print('Serializer - dump: ' + str(time.time() - s))
    #
    # s = time.time()
    # for i in range(500):
    #     data2 = schema.dump(model).data
    # print('Marshmallow - dump: ' + str(time.time() - s))

    models = [Model() for i in range(500)]

    serializer = ModelSchema()
    schema = MM_ModelSchema(many=True)

    s = time.time()
    data = serializer.dumps(models)
    print('WebAPI - dump: ' + str(time.time() - s))

    s = time.time()
    data2 = schema.dump(models).data
    print('Marshmallow - dump: ' + str(time.time() - s))

    s = time.time()
    serializer.loads(data)
    print('WebAPI - load: ' + str(time.time() - s))

    s = time.time()
    d = schema.load(data2)
    print('Marshmallow - load: ' + str(time.time() - s))
