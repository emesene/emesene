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
    def __init__(self, max=10):
        self.max = max
        self.items = ["",]
        self.pos = 0

    def pop(self):
        '''remove the head of the buffer and return it'''
        item = self.items.pop(1)
        return item

    def push(self, item):
        '''add an element to the buffer and set it as the head of
        the buffer'''

        if len(self.items) + 1 < self.max:
            self.items.append(item)
        elif len(self.items) - 1 < self.max:
            self.items.append(item)
            self.pop()

    def peak(self, offset=0):
        '''return the item that is in head + offset, doesn't remove it'''
        if len(self.items) == 1:
            raise IndexError("peaking an empty RingBuffer")
            
        self.pos = offset
        return self.items[self.pos]

    def __len__(self):
        '''return the current size of the buffer'''
        return len(self.items)

