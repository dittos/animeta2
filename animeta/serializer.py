import calendar
import datetime
from flask import json
from animeta import models

class ObjectSerializerMeta(type):
    serializers = []

    def __new__(self, name, bases, dict):
        cls = type.__new__(self, name, bases, dict)
        if 'cls' in dict:
            self.serializers.append(cls())
        return cls

    @classmethod
    def serialize(self, obj):
        for serializer in self.serializers:
            if isinstance(obj, serializer.cls):
                return serializer(obj)
        raise TypeError(repr(obj))

class ObjectSerializer(object):
    __metaclass__ = ObjectSerializerMeta

    def __call__(self, obj):
        d = {}
        for field in self.fields:
            d[field] = getattr(obj, field)
        return d

class LibraryItemSerializer(ObjectSerializer):
    cls = models.LibraryItem
    fields = ('id', 'title', 'progress', 'status', 'updated_at')

def default(obj):
    try:
        iterable = iter(obj)
    except TypeError:
        if isinstance(obj, datetime.datetime):
            return calendar.timegm(obj.utctimetuple())
        return ObjectSerializerMeta.serialize(obj)
    else:
        return list(iterable)
    raise TypeError(obj)

def serialize(obj):
    return json.dumps(obj, default=default)
