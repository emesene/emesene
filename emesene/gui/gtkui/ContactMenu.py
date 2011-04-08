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

import gtk

class ContactMenu(gtk.Menu):
    """
    A class that represents a menu to handle contact related information
    """
    NAME = 'Contact Menu'
    DESCRIPTION = 'The menu that displays contact options'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, handler):
        """
        constructor

        handler -- a e3common.Handler.ContactHandler
        """
        gtk.Menu.__init__(self)
        self.handler = handler

        self.add = gtk.ImageMenuItem(gtk.STOCK_ADD)
        self.add.connect('activate',
            lambda *args: self.handler.on_add_contact_selected())

        self.remove = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        self.remove.connect('activate',
            lambda *args: self.handler.on_remove_contact_selected())

        self.block = gtk.ImageMenuItem(_('Block'))
        self.block.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL,
            gtk.ICON_SIZE_MENU))
        self.block.connect('activate',
            lambda *args: self.handler.on_block_contact_selected())

        self.unblock = gtk.ImageMenuItem(_('Unblock'))
        self.unblock.set_image(gtk.image_new_from_stock(gtk.STOCK_APPLY,
            gtk.ICON_SIZE_MENU))
        self.unblock.connect('activate',
            lambda *args: self.handler.on_unblock_contact_selected())

        self.set_alias = gtk.ImageMenuItem(_('Set alias'))
        self.set_alias.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT,
            gtk.ICON_SIZE_MENU))
        self.set_alias.connect('activate',
            lambda *args: self.handler.on_set_alias_contact_selected())

        self.view_info = gtk.ImageMenuItem(_('View information'))
        self.view_info.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT,
            gtk.ICON_SIZE_MENU))
        self.view_info.connect('activate',
            lambda *args: self.handler.on_view_information_selected())

        all_groups = self.handler.get_all_groups()
        contact_groups = self.handler.get_contact_groups()
        self.move_groups_submenu = gtk.Menu()
        self.copy_groups_submenu = gtk.Menu()
        for group in all_groups:
            if group not in contact_groups:
                item = gtk.MenuItem(group)
                item.connect('activate', 
                    lambda *args: self.handler.on_move_to_group_selected(group))
                self.move_groups_submenu.append(item)
                item_2 = gtk.MenuItem(group)
                item_2.connect('activate', 
                    lambda *args: self.handler.on_copy_to_group_selected(group))
                self.copy_groups_submenu.append(item_2)

        self.move_to_group = gtk.ImageMenuItem(_('Move to group'))
        self.move_to_group.set_image(gtk.image_new_from_stock(gtk.STOCK_GO_FORWARD,
            gtk.ICON_SIZE_MENU))
        self.move_to_group.set_submenu(self.move_groups_submenu)

        self.copy_to_group = gtk.ImageMenuItem(_('Copy to group'))
        self.copy_to_group.set_image(gtk.image_new_from_stock(gtk.STOCK_COPY,
            gtk.ICON_SIZE_MENU))
        self.copy_to_group.set_submenu(self.copy_groups_submenu)

        if len(contact_groups) > 1:
            self.remove_from_group = gtk.ImageMenuItem(_('Remove from group'))
            self.remove_from_group.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE,
                gtk.ICON_SIZE_MENU))
            self.remove_from_group.connect('activate',
                lambda *args: self.handler.on_remove_from_group_selected())

        self.set_unblocked()

        self.append(self.add)
        self.append(self.remove)
        self.append(self.block)
        self.append(self.unblock)
        self.append(self.set_alias)
        self.append(self.view_info)
        #self.append(self.move_to_group)
        #self.append(self.copy_to_group)
        #if len(contact_groups) > 1:
        #    self.append(self.remove_from_group)

    def set_blocked(self):
        self.unblock.set_sensitive(True)
        self.block.set_sensitive(False)

    def set_unblocked(self):
        self.unblock.set_sensitive(False)
        self.block.set_sensitive(True)

