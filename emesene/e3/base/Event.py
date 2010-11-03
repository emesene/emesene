# -*- coding: utf-8 -*-
'''a module that defines an event object'''

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

class Event(object):
    '''an object that represents an event'''

    def __init__(self, id_, *args):
        '''class constructor'''
        self.id_ = id_

        if args is None:
            self.args = []
        else:
            self.args = args

    def dict(self):
        '''return a dict representing the object'''
        return dict(id_ = self.id_, 
            args = self.args)

    @classmethod
    def set_constants(cls, events):
        '''creates an event class that has the event list as constants starting
        with EVENT_ and an uppercase string replacing the spaces with 
        underscores
        '''
        sorted = list(events)
        sorted.sort()
        events = tuple(sorted)

        for (index, event) in enumerate(events):
            setattr(cls, 'EVENT_' + event.upper().replace(' ', '_'), index)
