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

        self.move_groups_submenu = gtk.Menu()
        self.copy_groups_submenu = gtk.Menu()
        self.remove_group_submenu = gtk.Menu()

        self.move_to_group = gtk.ImageMenuItem(_('Move to group'))
        self.move_to_group.set_image(gtk.image_new_from_stock(gtk.STOCK_GO_FORWARD,
            gtk.ICON_SIZE_MENU))
        self.move_to_group.connect('activate', 
                    lambda *args: self.on_move_to_group())
        self.move_to_group.set_submenu(self.move_groups_submenu)

        self.copy_to_group = gtk.ImageMenuItem(_('Copy to group'))
        self.copy_to_group.set_image(gtk.image_new_from_stock(gtk.STOCK_COPY,
            gtk.ICON_SIZE_MENU))
        self.copy_to_group.connect('activate', 
                    lambda *args: self.on_copy_to_group())
        self.copy_to_group.set_submenu(self.copy_groups_submenu)

        self.remove_from_group = gtk.ImageMenuItem(_('Remove from group'))
        self.remove_from_group.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE,
            gtk.ICON_SIZE_MENU))
        self.remove_from_group.connect('activate',
            lambda *args: self.on_remove_from_group())
        self.remove_from_group.set_submenu(self.remove_group_submenu)
        self.groups_to_remove = 0

        self.view_info = gtk.ImageMenuItem(_('View information'))
        self.view_info.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT,
            gtk.ICON_SIZE_MENU))
        self.view_info.connect('activate',
            lambda *args: self.handler.on_view_information_selected())
            
        self.account_to_clipboard = gtk.ImageMenuItem(_('Copy mail to clipboard'))
        self.account_to_clipboard.set_image(gtk.image_new_from_stock(gtk.STOCK_COPY,
            gtk.ICON_SIZE_MENU))
        self.account_to_clipboard.connect('activate',
            lambda *args: self.on_copy_account_to_clipboard())

        self.set_unblocked()

        self.append(self.add)
        self.append(self.remove)
        self.append(self.block)
        self.append(self.unblock)
        self.append(self.set_alias)
        self.append(self.move_to_group)
        self.append(self.copy_to_group)
        self.append(self.remove_from_group)
        self.append(self.account_to_clipboard)
        self.append(self.view_info)

    def on_copy_account_to_clipboard(self):
        contact = self.handler.contact_list.get_contact_selected()
        
        if contact:
            clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(contact.account)

    def on_move_to_group(self):
        self.update_submenus()

    def on_copy_to_group(self):
        self.update_submenus()

    def on_remove_from_group(self):
        self.update_submenus()

    def update_submenus(self):
        for i in self.move_groups_submenu.get_children():
            self.move_groups_submenu.remove(i)
        for i in self.copy_groups_submenu.get_children():
            self.copy_groups_submenu.remove(i)
        for i in self.remove_group_submenu.get_children():
            self.remove_group_submenu.remove(i)
        self.groups_to_remove = 0

        if not self.handler.is_by_group_view(): return

        all_groups = self.handler.get_all_groups()
        contact_groups = self.handler.get_contact_groups()

        for key, group in all_groups.iteritems():
            if key not in contact_groups:
                item = gtk.MenuItem(group.name)
                item.connect('activate', 
                    self.on_move_to_group_selected, group)
                self.move_groups_submenu.append(item)
                item_2 = gtk.MenuItem(group.name)
                item_2.connect('activate', 
                    self.on_copy_to_group_selected, group)
                self.copy_groups_submenu.append(item_2)
            else:
                self.groups_to_remove = 1
                item = gtk.MenuItem(group.name)
                item.connect('activate', 
                    self.on_remove_from_group_selected, group)
                self.remove_group_submenu.append(item)

        self.move_groups_submenu.show_all()
        self.copy_groups_submenu.show_all()
        self.remove_group_submenu.show_all()

        self.copy_to_group.set_sensitive(self.groups_to_remove)
        self.remove_from_group.set_sensitive(self.groups_to_remove)

    def on_copy_to_group_selected(self, widget, group):
        self.handler.on_copy_to_group_selected(group)

    def on_move_to_group_selected(self, widget, group):
        self.handler.on_move_to_group_selected(group)

    def on_remove_from_group_selected(self, widget, group):
        self.handler.on_remove_from_group_selected(group)

    def set_blocked(self):
        self.unblock.show()
        self.block.hide()

    def set_unblocked(self):
        self.unblock.hide()
        self.block.show()

