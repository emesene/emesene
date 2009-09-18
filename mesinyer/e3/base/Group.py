# -*- coding: utf-8 -*-
'''a module that defines a group object'''

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
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

    def __init__(self, name, identifier=None, contacts=None):
        '''class constructor'''
        self.name = name
        self.identifier = identifier or '0'
        self.contacts = contacts or []

    def dict(self):
        '''return a dict representing the object'''
        return dict(name = self.name,
          identifier = self.identifier,
          contacts = self.contacts)

    def _on_contact_added(self, account):
        '''callback called when a contact is added to this group'''
        self.contacts.append(account)

    def _on_contact_removed(self, account):
        '''callback called when a contact is removed from this group'''
        if account in self.contacts:
            del self.contacts[account]

    def __repr__(self):
        '''return a string representation of the object'''
        return "<group name='%s'>" % (self.name,)
