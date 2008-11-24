# -*- coding: utf-8 -*-

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
'''a class that represent a contextual menu to select a status'''

import Menu
import gui

import protocol.status as status

class StatusMenu(Menu.Menu):
    '''a class that represents a menu popup to select a status'''

    def __init__(self, contacts, callback):
        '''class constructor'''
        Menu.Menu.__init__(self)

        self.contacts = contacts
        self.callback = callback

        self.some_list = []

        for stat in status.ORDERED:
            temp_item = Menu.Item(status.STATUS[stat], 
                Menu.Item.TYPE_IMAGE_PATH, 
                gui.theme.status_icons[stat])
            temp_item.signal_connect('selected', 
                self._on_status_selected, stat)
            self.append(temp_item)
            self.some_list.append(temp_item.signals)

    def _on_status_selected(self, item, stat):
        '''called when a status is selected'''
        if self.contacts != None:
            self.contacts.set_status(stat)
        self.callback(stat)

