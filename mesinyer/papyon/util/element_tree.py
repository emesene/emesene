# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2007 Johann Prieur <johann.prieur@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

"""ElementTree independent from the available distribution"""

try:
    from xml.etree.cElementTree import * 
except ImportError:
    try:
        from cElementTree import *
    except ImportError:
        from elementtree.ElementTree import *

__all__ = ["XMLTYPE", "XMLResponse"]

import iso8601

class XMLTYPE(object):

    class bool(object):
        @staticmethod
        def encode(boolean):
            if boolean:
                return "true"
            return "false"

        @staticmethod
        def decode(boolean_str):
            false_set = ("false", "f", "no", "n", "0", "")
            if str(boolean_str).strip().lower() not in false_set:
                return True
            return False

    class int(object):
        @staticmethod
        def encode(integer):
            return str(integer)

        @staticmethod
        def decode(integer_str):
            try:
                return int(integer_str)
            except ValueError:
                return 0

    class datetime(object):
        @staticmethod
        def encode(datetime):
            return datetime.isoformat()

        @staticmethod
        def decode(date_str):
            result = iso8601.parse_date(date_str.strip())
            return result.replace(tzinfo=None) # FIXME: do not disable the timezone

class _Element(object):
    def __init__(self, element, ns_shorthands):
        self.element = element
        self.ns_shorthands = ns_shorthands.copy()

    def __getattr__(self, name):
        return getattr(self.element, name)

    def __getitem__(self, name):
        return self.element[name]

    def __iter__(self):
        for node in self.element:
            yield _Element(node, self.ns_shorthands)

    def __contains__(self, node):
        return node in self.element

    def __repr__(self):
        return "<Element name=\"%s\">" % (self.element.tag,)

    def _process_path(self, path):
        for sh, ns in self.ns_shorthands.iteritems():
            path = path.replace("/%s:" % sh, "/{%s}" % ns)
            if path.startswith("%s:" % sh):
                path = path.replace("%s:" % sh, "{%s}" % ns, 1)
        return path

    def find(self, path):
        path = self._process_path(path)
        node = self.element.find(path)
        if node is None:
            return None
        return _Element(node, self.ns_shorthands)

    def findall(self, path):
        path = self._process_path(path)
        
        result = []
        nodes = self.element.findall(path)
        for node in nodes:
            result.append(_Element(node, self.ns_shorthands))
        return result

    def findtext(self, path, type=None):
        result = self.find(path)
        if result is None:
            return ""
        result = result.text
        
        if type is None:
            return result
        return getattr(XMLTYPE, type).decode(result)

class XMLResponse(object):

    def __init__(self, data, ns_shorthands={}):
        try:
            tree = self._parse(data)
            self.tree = _Element(tree, ns_shorthands)
        except:
            self.tree = None

    def __getitem__(self, name):
        return self.tree[name]

    def find(self, path):
        return self.tree.find(path)

    def findall(self, path):
        return self.tree.findall(path)
    
    def findtext(self, path, type=None):
        return self.tree.findtext(path, type)

    def is_valid(self):
        return self.tree is not None

    def _parse(self, data):
        pass
