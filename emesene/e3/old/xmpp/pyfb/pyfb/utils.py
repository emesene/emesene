"""
    $Id: utils.py

    This file provides utilities to the pyfb library
"""

try:
    import json as simplejson
except ImportError:
    import simplejson

import urllib2


class FacebookObject(object):
    """
        Builds an object of a runtime generated class with a name
        passed by argument.
    """
    def __new__(cls, name):
        return type(str(name), (object, ), {})


class PaginatedList(list):

    def __init__(self, objs=None, parent=None, object_name=None):

        if objs is not None:
            self.extend(objs)

        factory = Json2ObjectsFactory()

        def _get_page(page):

            paging = getattr(parent, "paging", False)
            if not paging:
                return PaginatedList()

            url = getattr(paging, page, False)
            if not url:
                return PaginatedList()

            obj = factory.make_object(object_name, urllib2.urlopen(url).read())
            objs_list = factory.make_paginated_list(obj, object_name)

            if not objs_list:
                return PaginatedList()

            return objs_list

        self.next = lambda: _get_page("next")
        self.previous = lambda: _get_page("previous")


class Json2ObjectsFactory(object):
    """
        Converts a json-like dictionary into an object.

        It navigates recursively into the dictionary turning
        everything into an object.
    """

    def loads(self, data):
        return simplejson.loads(data)

    def make_object(self, name, data):
        raw = self.loads(data)
        return self._make_object(name, raw)

    def make_objects_list(self, name, data):
        raw = self.loads(data)
        return self._make_objects_list(name, raw)

    def make_paginated_list(self, obj, object_name):

        objs = getattr(obj, object_name, False)
        if not objs:
            return False

        objs_list = PaginatedList(objs, obj, object_name)
        return objs_list

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
        obj = FacebookObject(name)
        for key, value in dic.iteritems():
            if key == 'data':
                key = obj.__name__
            if isinstance(value, list):
                value = self._make_objects_list(key, value)
            elif isinstance(value, dict):
                value = self._make_object(key, value)
            setattr(obj, key, value)
        return obj
