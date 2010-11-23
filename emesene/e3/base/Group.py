# -*- coding: utf-8 -*-
'''a module that defines a group object'''

#   This file is part of emesene.
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

class Group(object):
    '''a class representing a group'''
    (ONLINE, OFFLINE, NONE, STANDARD) = range(4)
    def __init__(self, name, identifier=None, contacts=None, type_=None):
        '''class constructor'''
        self.name = name
        self.identifier = identifier or '0'
        self.contacts = contacts or []
        self.type = type_ or Group.STANDARD

    def dict(self):
        '''return a dict representing the object'''
        return dict(type_ = self.type, 
          name = self.name,
          identifier = self.identifier,
          contacts = self.contacts)

    def __repr__(self):
        '''return a string representation of the object'''
        return "<group name='%s'>" % (self.name,)
