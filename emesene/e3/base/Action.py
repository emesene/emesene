# -*- coding: utf-8 -*-
'''a module that defines an action object'''

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

class Action(object):
    '''this class represent an action that must be performed by the server'''

    def __init__(self, id_, args=None):
        '''class constructor'''
        self.id_ = id_
        
        if args is not None:
            self.args = args
        else:
            self.args = []
    
    @classmethod
    def set_constants(cls, actions):
        '''creates an event class that has the event list as constants starting
        with EVENT_ and an uppercase string replacing the spaces with 
        underscores
        '''
        for (index, action) in enumerate(actions):
            setattr(cls, 'ACTION_' + action.upper().replace(' ', '_'), index)
