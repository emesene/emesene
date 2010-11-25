'''e3.Call handling module'''
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

class Call(object):
    '''a class that represent a call'''
    (WAITING, INVITING, INVITED, ESTABLISHED, FAILED) = range(5)

    def __init__(self, obj, peer):
        self.object = obj
        self.state = Call.WAITING
        self.peer = peer

        self.time_start = 0

        self.surface_buddy = None
        self.surface_self = None

    def __str__(self):
        '''return a string representation of a call'''
        return '<e3.base.Call state="%i" peer="%s">' % (self.state, self.peer)

