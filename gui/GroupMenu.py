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
'''a class that represent a contextual menu of a group'''

import Menu
import protocol.base.stock as stock

# TODO: remove this
_ = lambda x: x

class GroupMenu(Menu.Menu):
    '''class that represent a contextual menu of a group'''

    def __init__(self, group, groups, contacts, dialog):
        '''class constructor'''
        Menu.Menu.__init__(self)

        self.group = group
        self.groups = groups
        self.contacts = contacts
        self.dialog = dialog
        
        self._build()

    def _build(self):
        '''build the menu'''
        self.remove_item = Menu.Item(_('_Remove'), Menu.Item.TYPE_STOCK, 
            stock.REMOVE)
        self.remove_item.signal_connect('selected', self._on_remove_selected)
        
        self.rename_item = Menu.Item(_('Re_name'), Menu.Item.TYPE_STOCK, 
            stock.EDIT)
        self.rename_item.signal_connect('selected', self._on_rename_selected)

        self.add_item = Menu.Item(_('_Add contact'), Menu.Item.TYPE_STOCK, 
            stock.ADD)
        self.add_item.signal_connect('selected', self._on_add_selected)

        self.append(self.remove_item)
        self.append(self.rename_item)
        self.append(self.add_item)
    
    def _on_remove_selected(self, item):
        '''called when remove is selected'''
        def _yes_no_cb(response):
            '''callback from the confirmation dialog'''
            if response == stock.YES:
                self.groups.remove(self.groups.name)

        self.dialog.yes_no(
            _('Are you sure you want to remove group %s?') % \
            (self.group.name,), _yes_no_cb)

    def _on_rename_selected(self, item):
        '''called when rename is selected'''
        self.groups.rename_dialog(self.group.name)
    
    def _on_add_selected(self, item):
        '''called when rename is selected'''
        def add_contact_cb(response, account='', group=''):
            '''callback for the add_contact dialog'''
            if response == stock.ACCEPT:
                if account:
                    self.contacts.add(account)

                    if group:
                        self.contacts.add_to_group(account, group)
                else:
                    self.dialog.warning(_("Empty account"))

        self.dialog.add_contact(self.groups.groups.keys(), self.group.name, 
            add_contact_cb)

