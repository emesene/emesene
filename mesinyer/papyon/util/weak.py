# -*- coding: utf-8 -*-
#
# Copyright (C) 2009  Collabora Ltd.
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

"""Some missing weak refs"""

from weakref import WeakValueDictionary

__all__ = ['WeakSet']

class WeakSet(object):

    def __init__(self):
        self._data = WeakValueDictionary()

    def add(self, obj):
        self._data[id(obj)] = obj

    def remove(self, obj):
        try:
            del self._data[id(obj)]
        except:
            raise KeyError(obj)

    def discard(self, obj):
        try:
            self.remove(obj)
        except:
            return

    def __iter__(self):
        for obj in self._data.values():
            yield obj

    def __len__(self):
        return len(self._data)

    def __contains__(self, obj):
        return id(obj) in self._data

    def __hash__(self):
        raise TypeError, "Can't hash a WeakSet."
