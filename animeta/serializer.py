import calendar
import collections
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
    def serialize(self, obj, **kwargs):
        for serializer in self.serializers:
            if isinstance(obj, serializer.cls):
                return serializer(obj, **kwargs)
        raise TypeError(repr(obj))

serialize_object = ObjectSerializerMeta.serialize

class ObjectSerializer(object):
    __metaclass__ = ObjectSerializerMeta

    def __call__(self, obj, exclude_fields=(), include_fields=()):
        d = {}
        fields = set(self.fields).union(set(include_fields)) - set(exclude_fields)
        for field in fields:
            try:
                v = getattr(self, field)(obj)
            except AttributeError:
                v = getattr(obj, field)
            d[field] = v
        return d

class UserSerializer(ObjectSerializer):
    cls = models.User
    fields = ('id', 'username')

    def items(self, obj):
        return obj.library_items.order_by(models.LibraryItem.updated_at.desc().nullslast())

class LibraryItemSerializer(ObjectSerializer):
    cls = models.LibraryItem
    fields = ('id', 'user_id', 'title', 'progress', 'status', 'updated_at')

    def updates(self, obj):
        return obj.updates.order_by(models.Update.id.desc())

class UpdateSerializer(ObjectSerializer):
    cls = models.Update
    fields = ('id', 'item_id', 'progress', 'status', 'updated_at', 'comment')

    def item_id(self, obj):
        return obj.library_item.id

def default(obj):
    try:
        iterable = iter(obj)
    except TypeError:
        if isinstance(obj, datetime.datetime):
            return calendar.timegm(obj.utctimetuple())
        return serialize_object(obj)
    else:
        return list(iterable)
    raise TypeError(obj)

def serialize(obj, **kwargs):
    if isinstance(obj, collections.Iterable):
        result = map(lambda o: serialize_object(o, **kwargs), obj)
    else:
        result = serialize_object(obj, **kwargs)
    return json.dumps(result, default=default,
            ensure_ascii=False, separators=(',', ':'))
