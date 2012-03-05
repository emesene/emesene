"""
    $Id: utils.py

    This file provides utilities to the pyfb library
"""

import simplejson

class NamedObject(object):
    """
        Builds an object of a runtime generated class with a name
        passed by argument.
    """
    def __new__(cls, name):
        return type(str(name), (object, ), {})


class Json2ObjectsFactory(object):
    """
        Converts a json-like dictionary into an object.

        It navigates recursively into the dictionary turning
        everything into an object.
    """

    def loads(self, data):
        return simplejson.loads(data)

    def make_object(self, name, data):
        raw = simplejson.loads(data)
        return self._make_object(name, raw)

    def make_objects_list(self, name, data):
        raw = simplejson.loads(data)
        return self._make_objects_list(name, raw)

    def _make_objects_list(self, name, values):
        objs = []
        for data in values:
            if isinstance(data, dict):
                objs.append(self._make_object(name, data))
            else:
                objs.append(data)
        return objs

    def _make_object(self, name, dic):
        #Life's easy. For Python Programmers BTW ;-).
        obj = NamedObject(name)
        for key, value in dic.iteritems():
            if key == 'data':
                key = obj.__name__
            if isinstance(value, list):
                value = self._make_objects_list(key, value)
            elif isinstance(value, dict):
                value = self._make_object(key, value)
            setattr(obj, key, value)
        return obj
