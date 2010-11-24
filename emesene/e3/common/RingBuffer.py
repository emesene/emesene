# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

class RingBuffer(object):
    def __init__(self, max=5):
        self.max = max
        self.items = []
        self.current = 0

    def pop(self):
        '''remove the head of the buffer and return it'''
        item = self.items.pop(self.current)

        self.current -= 1

        if self.current < 0:
            self.current = len(self.items) - 1

        return item

    def push(self, item):
        '''add an element to the buffer and set it as the head of
        the buffer'''
        if len(self.items) < self.max:
            self.items.append(item)
            self.current = len(self.items) - 1
        elif self.current == self.max - 1:
            self.items[0] = item
            self.current = 0
        else:
            self.items[self.current + 1] = item
            self.current += 1

    def peak(self, offset=0):
        '''return the item that is in head + offset, doesn't remove it'''
        if len(self.items) == 0:
            raise IndexError("peaking an empty RingBuffer")

        pos = self.current + offset

        if pos < 0 or pos > len(self.items) - 1:
            pos = pos % len(self.items)

        return self.items[pos]

    def __len__(self):
        '''return the current size of the buffer'''
        return len(self.items)

