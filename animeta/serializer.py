import calendar
import datetime
import re
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

UNDERSCORE_RE = re.compile('_([a-z])')

class ObjectSerializer(object):
    __metaclass__ = ObjectSerializerMeta

    def __init__(self):
        self._out_field_names = {}
        for field in self.fields:
            out_field = UNDERSCORE_RE.sub(lambda m: m.group(1).upper(), field)
            self._out_field_names[field] = out_field

    def __call__(self, obj):
        d = {}
        for field in self.fields:
            d[self._out_field_names[field]] = getattr(obj, field)
        return d

class LibraryItemSerializer(ObjectSerializer):
    cls = models.LibraryItem
    fields = ('id', 'user_id', 'title', 'progress', 'status', 'updated_at')

class UpdateSerializer(ObjectSerializer):
    cls = models.Update
    fields = ('id', 'progress', 'status', 'updated_at', 'comment')

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
    return json.dumps(obj, default=default, ensure_ascii=False, separators=(',', ':'))
