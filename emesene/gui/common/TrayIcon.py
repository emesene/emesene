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

import os
import sys
import gtk
import time
import gobject

import extension
from e3 import status

import gui
import gui.gtkui.utils as utils

class TrayIcon(gtk.StatusIcon, gui.BaseTray):
    """
    A widget that implements the tray icon of emesene for gtk
    """
    NAME = 'Tray Icon'
    DESCRIPTION = 'The gtk tray icon'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, handler, main_window=None):
        """
        constructor

        handler -- a e3common.Handler.TrayIconHandler object
        """
        gui.BaseTray.__init__(self, handler)
        gtk.StatusIcon.__init__(self)

        self.main_window = main_window
        self.last_new_message = None

        self.connect('activate', self._on_activate)
        self.connect('popup-menu', self._on_popup)

        self.set_login()
        gui.BaseTray.set_visible(self, True)
        gtk.StatusIcon.set_visible(self, True)

        self.set_tooltip("emesene")

    def set_login(self):
        """
        method called to set the state to the login window
        """
        self.menu = LoginMenu(self.handler, self.main_window)
        self.menu.show_all()
        self.set_from_file(self.handler.theme.image_theme.logo_panel)

    def set_main(self, session):
        """
        method called to set the state to the main window
        """
        gui.BaseTray.set_main(self, session)
        self.menu = MainMenu(self.handler, self.main_window)
        self.menu.show_all()
        self.set_tooltip("emesene - " + self.handler.session.account.account)
        self._on_status_change_succeed(self.handler.session.account.status)

    def _on_conv_message(self, cid, account, msgobj, cedict=None):
        """
        Blink tray icon and save newest unread message
        """

        conv_manager = self._get_conversation_manager(cid, account)

        if conv_manager and not conv_manager.is_active():
            self.set_blinking(True)
            self.last_new_message = cid

    def _on_message_read(self, conv):
        """
        Stop tray blinking and resets the newest unread message reference
        """
        self.set_blinking(False)
        self.last_new_message = None

    def _on_activate(self, trayicon):
        """
        callback called when the status icon is activated
        (includes clicking the icon)
        """

        if self.last_new_message is not None and self.get_blinking():
            # show the tab with the latest message
            cid = self.last_new_message
            conv_manager = self._get_conversation_manager(cid)

            if conv_manager:
                conversation = conv_manager.conversations[cid]
                conv_manager.present(conversation)
        else:
            self.handler.on_hide_show_mainwindow(self.main_window)

    def _on_status_change_succeed(self, stat):
        """
        change the icon in the tray according to user's state
        """
        if stat not in status.ALL or stat == -1:
            return
        self.set_from_file(self.handler.theme.image_theme.status_icons_panel[stat])

    def _on_popup(self, trayicon, button, activate_time):
        """
        callback called when the popup of the status icon is activated
        (usually through right-clicking the status icon)
        """
        position = None
        if os.name == 'mac' or sys.platform == 'linux2' or sys.platform == 'linux3':
            position = gtk.status_icon_position_menu
        self.menu.popup(None, None, position, button, activate_time, trayicon)

    def _on_contact_attr_changed(self, *args):
        """
        This is called when a contact changes something
        """
        self.menu.list_contacts._on_contact_change_something(*args)

class LoginMenu(gtk.Menu):
    """
    a widget that represents the menu displayed on the trayicon on the
    login window
    """

    def __init__(self, handler, main_window=None):
        """
        constructor

        handler -- a e3common.Handler.TrayIconHandler object
        """
        gtk.Menu.__init__(self)
        self.handler = handler
        self.hide_show_mainwindow = gtk.MenuItem(_('Hide/Show emesene'))
        self.hide_show_mainwindow.connect('activate',
            lambda *args: self.handler.on_hide_show_mainwindow(main_window))
        self.quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        self.quit.connect('activate',
            lambda *args: self.handler.on_quit_selected())

        self.append(self.hide_show_mainwindow)
        self.append(self.quit)

class MainMenu(gtk.Menu):
    """
    a widget that represents the menu displayed on the trayicon on the
    main window
    """

    def __init__(self, handler, main_window=None):
        """
        constructor

        handler -- a e3common.Handler.TrayIconHandler object
        """
        gtk.Menu.__init__(self)
        self.handler = handler

        StatusMenu = extension.get_default('menu status')
        self.status = gtk.ImageMenuItem(_('Status'))
        self.status.set_image(gtk.image_new_from_stock(gtk.STOCK_CONVERT,
            gtk.ICON_SIZE_MENU))
        self.status_menu = StatusMenu(handler.on_status_selected)
        self.status.set_submenu(self.status_menu)

        self.list = gtk.ImageMenuItem(_('Contacts'))
        self.list.set_image(utils.safe_gtk_image_load(gui.theme.image_theme.chat))
        self.list_contacts = ContactsMenu(handler, main_window)
        self.list.set_submenu(self.list_contacts)

        self.hide_show_mainwindow = gtk.MenuItem(_('Hide/Show emesene'))
        self.hide_show_mainwindow.connect('activate',
            lambda *args: self.handler.on_hide_show_mainwindow(main_window))

        self.disconnect = gtk.ImageMenuItem(gtk.STOCK_DISCONNECT)
        self.disconnect.connect('activate',
            lambda *args: self.handler.on_disconnect_selected())
        self.quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        self.quit.connect('activate',
            lambda *args: self.handler.on_quit_selected())

        self.append(self.hide_show_mainwindow)
        self.append(self.status)
        self.append(self.list)
        self.append(self.disconnect)
        self.append(gtk.SeparatorMenuItem())
        self.append(self.quit)

class ContactsMenu(gtk.Menu):
    """
    a gtk menu that contains session's contacts
    """
    NAME = 'Contacts Menu'
    DESCRIPTION = _('A menu with sessions\' contacts')
    AUTHOR = 'Riccardo (C10uD)'
    WEBSITE = 'www.emesene.org'

    def __init__(self, handler, main_window=None):
        """
        constructor
        """
        gtk.Menu.__init__(self)
        self.handler = handler
        self.main_window = main_window
        self.item_to_contacts = {}
        self.contacts_to_item = {}
        self.avatar_size = 20

        self.contactmanager = self.handler.session.contacts

        for contact in self.contactmanager.get_online_list():
            self.__append_contact(contact)

    def __append_contact(self, contact):
        """
        appends a contact to our submenu
        """
        item = gtk.ImageMenuItem()
        item.set_label(gui.Plus.msnplus_strip(contact.nick))
        pict = self.__get_contact_pixbuf_or_default(contact)
        item.set_image(pict)
        item.connect('activate', self._on_contact_clicked)
        self.item_to_contacts[item] = contact
        self.contacts_to_item[contact.account] = item

        item.show()
        self.add(item)

    def _on_contact_change_something(self, *args):
        """
        update the menu when contacts change something
        """
        if len(args) == 3:
            account, type_change, value_change = args
        elif len(args) == 4:
            account, type_change, value_change, do_notify = args

        if type_change == 'status':
            if value_change > 0:
                if account in self.contacts_to_item:
                    return
                self.__append_contact(self.contactmanager.get(account))
            else: # offline
                if account in self.contacts_to_item:
                    self.remove(self.contacts_to_item[account])
                    del self.item_to_contacts[self.contacts_to_item[account]]
                    del self.contacts_to_item[account]

        if type_change == 'nick':
            if account in self.contacts_to_item:
                nick = self.item_to_contacts[self.contacts_to_item[account]].nick
                self.contacts_to_item[account].set_label(nick)

        if type_change == 'picture':
        #TODO: fixme
            return
            if account in self.contacts_to_item:
                contact = self.item_to_contacts[self.contacts_to_item[account]]
                pict = self.__get_contact_pixbuf_or_default(contact)
                self.contacts_to_item[account].set_image(pict)

    def _on_contact_clicked(self, menu_item):
        """
        called when contacts are clicked
        """
        acc = self.item_to_contacts[menu_item].account
        cid = time.time()
        self.main_window.content.on_new_conversation(cid, [acc], other_started=False)
        self.handler.session.new_conversation(acc, cid)

    def __get_contact_pixbuf_or_default(self, contact):
        '''try to return a pixbuf of the user picture or the default
        picture
        '''
        if contact.picture:
            try:
                animation = gtk.gdk.PixbufAnimation(contact.picture)
            except gobject.GError:
                pix = utils.safe_gtk_pixbuf_load(gui.theme.image_theme.user,
                        (self.avatar_size, self.avatar_size))
                picture = gtk.image_new_from_pixbuf(pix)
                return picture

            pix = animation.get_static_image()
            pix = pix.scale_simple(self.avatar_size, self.avatar_size,
                                   gtk.gdk.INTERP_BILINEAR)
            picture = gtk.image_new_from_pixbuf(pix)

        else:
            pix = utils.safe_gtk_pixbuf_load(gui.theme.image_theme.user,
                        (self.avatar_size, self.avatar_size))
            picture = gtk.image_new_from_pixbuf(pix)

        return picture
