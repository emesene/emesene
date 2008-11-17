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
'''a class that represent a contextual menu of a contact'''

import Menu
import protocol.stock as stock

# TODO: remove this
_ = lambda x: x

class ContactMenu(Menu.Menu):
    '''class that represent a contextual menu of a contact'''

    def __init__(self, contact, contacts, dialog):
        '''class constructor'''
        Menu.Menu.__init__(self)

        self.contact = contact
        self.contacts = contacts
        self.dialog = dialog
        
        self._build()

    def _build(self):
        '''build the menu'''
        self.remove_item = Menu.Item(_('_Remove'), Menu.Item.TYPE_STOCK, 
            stock.REMOVE)
        self.remove_item.signal_connect('selected', self._on_remove_selected)
        
        self.block_item = Menu.Item(_('_Block'), Menu.Item.TYPE_STOCK, 
            stock.STOP)
        self.block_item.signal_connect('selected', self._on_block_selected)
        
        self.unblock_item = Menu.Item(_('_Unblock'), Menu.Item.TYPE_STOCK, 
            stock.APPLY)
        self.unblock_item.signal_connect('selected', self._on_unblock_selected)
        
        self.move_item = Menu.Item(_('_Move'), Menu.Item.TYPE_STOCK, 
            stock.FORWARD)
        self.move_item.signal_connect('selected', self._on_move_selected)
        
        self.move_item = Menu.Item(_('_Copy'), Menu.Item.TYPE_STOCK, 
            stock.COPY)
        self.move_item.signal_connect('selected', self._on_copy_selected)

        self.set_alias_item = Menu.Item(_('Set _alias'), Menu.Item.TYPE_STOCK, 
            stock.EDIT)
        self.set_alias_item.signal_connect('selected', 
            self._on_set_alias_selected)
        
        self.append(self.remove_item)
        self.append(self.block_item)
        self.append(self.unblock_item)
        self.append(self.set_alias_item)
        self.append(self.move_item)
    
    def _on_remove_selected(self, item):
        '''called when remove is selected'''
        def _yes_no_cb(response):
            '''callback from the confirmation dialog'''
            if response == stock.YES:
                self.contacts.remove(self.contact.account)

        self.dialog.yes_no(
            _('Are you sure you want to remove contact %s?') % \
            (self.contact.account,), _yes_no_cb)

    def _on_block_selected(self, item):
        '''called when block is selected'''
        self.contacts.block(self.contact.account)

    def _on_unblock_selected(self, item):
        '''called when unblock is selected'''
        self.contacts.unblock(self.contact.account)

    def _on_move_selected(self, item):
        '''called when move is selected'''
        pass

    def _on_copy_selected(self, item):
        '''called when move is selected'''
        pass

    def _on_set_alias_selected(self, item):
        '''called when set_alias is selected'''
        self.contacts.set_alias_dialog(self.contact.account)
