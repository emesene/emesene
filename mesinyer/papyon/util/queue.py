# -*- coding: utf-8 -*-
#
# Copyright (C) 2006  Ali Sabil <ali.sabil@gmail.com>
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

"""Useful queues"""

__all__ = ['PriorityQueue', 'LastElementQueue']

import bisect

class PriorityQueue(object):
    def __init__(self, iterable=()):
        self.queue = list(iterable)

    def add(self, item, priority=0):
        bisect.insort(self.queue, (priority, item))

    def append(self, item):
        self.add(item)

    def pop(self, n):
        return self.queue.pop(n)[1]

    def __len__(self):
        return len(self.queue)

    @property
    def empty(self):
        return len(self.queue) == 0

class LastElementQueue(object):
    def __init__(self, iterable=()):
        self.queue = list(iterable)[-1:]

    def append(self, item):
        self.queue = [item]

    def pop(self, n):
        return self.queue.pop(n)

    def __len__(self):
        return len(self.queue)

    @property
    def empty(self):
        return len(self.queue) == 0



