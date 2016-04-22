"""
Makes main classes and decorators importable from flask-webapi
"""

from .api import WebAPI
from .decorators import allow_anonymous, authenticate, authorize, compat, param, route, serialize
