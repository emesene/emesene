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

import e3
import gtk
import gui
from gui.base import Plus

class ContactMenu(gtk.Menu):
    """
    A class that represents a menu to handle contact related information
    """
    NAME = 'Contact Menu'
    DESCRIPTION = 'The menu that displays contact options'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, handler, session):
        """
        constructor

        handler -- a e3common.Handler.ContactHandler
        """
        gtk.Menu.__init__(self)
        self.handler = handler
        self.session = session

        add = gtk.ImageMenuItem(gtk.STOCK_ADD)
        add.connect('activate',
            lambda *args: handler.on_add_contact_selected())

        remove = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        remove.connect('activate',
            lambda *args: handler.on_remove_contact_selected())

        self.block = gtk.ImageMenuItem(_('Block'))
        self.block.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL,
            gtk.ICON_SIZE_MENU))
        self.block.connect('activate',
            lambda *args: handler.on_block_contact_selected())

        self.unblock = gtk.ImageMenuItem(_('Unblock'))
        self.unblock.set_image(gtk.image_new_from_stock(gtk.STOCK_APPLY,
            gtk.ICON_SIZE_MENU))
        self.unblock.connect('activate',
            lambda *args: handler.on_unblock_contact_selected())

        set_alias = gtk.ImageMenuItem(_('Set alias'))
        set_alias.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT,
            gtk.ICON_SIZE_MENU))
        set_alias.connect('activate',
            lambda *args: handler.on_set_alias_contact_selected())

        self.move_groups_submenu = gtk.Menu()
        self.copy_groups_submenu = gtk.Menu()
        self.remove_group_submenu = gtk.Menu()

        move_to_group = gtk.ImageMenuItem(_('Move to group'))
        move_to_group.set_image(gtk.image_new_from_stock(gtk.STOCK_GO_FORWARD,
            gtk.ICON_SIZE_MENU))
        move_to_group.connect('activate', 
                    lambda *args: self.update_submenus())
        move_to_group.set_submenu(self.move_groups_submenu)

        self.copy_to_group = gtk.ImageMenuItem(_('Copy to group'))
        self.copy_to_group.set_image(gtk.image_new_from_stock(gtk.STOCK_COPY,
            gtk.ICON_SIZE_MENU))
        self.copy_to_group.connect('activate', 
                    lambda *args: self.update_submenus())
        self.copy_to_group.set_submenu(self.copy_groups_submenu)

        self.remove_from_group = gtk.ImageMenuItem(_('Remove from group'))
        self.remove_from_group.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE,
            gtk.ICON_SIZE_MENU))
        self.remove_from_group.connect('activate',
            lambda *args: self.update_submenus())
        self.remove_from_group.set_submenu(self.remove_group_submenu)
        self.groups_to_remove = 0

        view_info = gtk.ImageMenuItem(_('View information'))
        view_info.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT,
            gtk.ICON_SIZE_MENU))
        view_info.connect('activate',
            lambda *args: handler.on_view_information_selected())

        copy = gtk.ImageMenuItem(_('Copy contact information'))
        copy.set_image(gtk.image_new_from_stock(gtk.STOCK_COPY,
            gtk.ICON_SIZE_MENU))
        copy_menu = gtk.Menu()
        copy.set_submenu(copy_menu)
        account_to_clipboard = gtk.ImageMenuItem(_('Email address'))
        email_img = gtk.gdk.pixbuf_new_from_file_at_size(gui.theme.image_theme.email, 16, 16)
        account_to_clipboard.set_image(gtk.image_new_from_pixbuf(email_img))

        account_to_clipboard.connect('activate',
            lambda *args: self.on_copy_account_to_clipboard())

        nick_to_clipboard = gtk.ImageMenuItem(_('Nickname'))
        nick_img = gtk.gdk.pixbuf_new_from_file_at_size(gui.theme.image_theme.user, 16, 16)
        nick_to_clipboard.set_image(gtk.image_new_from_pixbuf(nick_img))

        nick_to_clipboard.connect('activate',
            lambda *args: self.on_copy_nick_to_clipboard())

        message_to_clipboard = gtk.ImageMenuItem(_('Personal message'))
        message_to_clipboard.set_image(gtk.image_new_from_stock(gtk.STOCK_DIALOG_INFO,
            gtk.ICON_SIZE_MENU))
        message_to_clipboard.connect('activate',
            lambda *args: self.on_copy_message_to_clipboard())

        self.set_unblocked()

        if self.session.session_has_service(e3.Session.SERVICE_CONTACT_MANAGING):
            self.append(add)
        if self.session.session_has_service(e3.Session.SERVICE_CONTACT_BLOCK):
            self.append(self.block)
            self.append(self.unblock)
        if self.session.session_has_service(e3.Session.SERVICE_CONTACT_MANAGING):
            self.append(remove)
            self.append(gtk.SeparatorMenuItem())
        if self.session.session_has_service(e3.Session.SERVICE_CONTACT_ALIAS):
            self.append(set_alias)
        self.append(view_info)
        self.append(gtk.SeparatorMenuItem())
        if self.session.session_has_service(e3.Session.SERVICE_GROUP_MANAGING):
            self.append(move_to_group)
            self.append(self.copy_to_group)
            self.append(self.remove_from_group)
            self.append(gtk.SeparatorMenuItem())
        self.append(copy)
        copy_menu.append(nick_to_clipboard)
        copy_menu.append(message_to_clipboard)
        copy_menu.append(account_to_clipboard)

    def on_copy_account_to_clipboard(self):
        contact = self.handler.contact_list.get_contact_selected()

        if contact:
            clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(contact.account)

    def on_copy_nick_to_clipboard(self):
        contact = self.handler.contact_list.get_contact_selected()

        if contact:
            clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(Plus.msnplus_strip(contact.nick))

    def on_copy_message_to_clipboard(self):
        contact = self.handler.contact_list.get_contact_selected()

        if contact:
            clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(Plus.msnplus_strip(contact.message))

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

        if all_groups:
            all_groups = sorted(all_groups.items(),
                             key = lambda x: Plus.msnplus_strip(x[1].name).lower())

        for key, group in all_groups:
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

