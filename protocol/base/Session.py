# -*- coding: utf-8 -*-
'''a module that defines a session object'''

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

import Queue

import Event
import ContactManager

class Session(object):
    
    def __init__(self, account):
        self.account = account
        self.extras = {}

        self.events = Queue.Queue()
        self.actions = Queue.Queue()

        self.contacts = ContactManager.ContactManager(self.account.account)
        self.groups = {}

    def add_event(self, id_, *args):
        '''add an event to the events queue'''
        self.events.put(Event(id_, tuple(args)))
