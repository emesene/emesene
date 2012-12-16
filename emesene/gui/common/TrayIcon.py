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
import gobject
import time

from gui.gtkui import check_gtk3
if check_gtk3():
    from gi.repository import Gio

import extension
import e3
from e3 import status

import gui
import gui.gtkui.utils as utils
import gui.gtkui.StatusMenu as StatusMenu

from gui import Plus
from NumerableTrayIcon import NumerableTrayIcon

class TrayIcon(gtk.StatusIcon, NumerableTrayIcon):
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

        handler -- a gui.base.Handler.TrayIconHandler object
        """
        NumerableTrayIcon.__init__(self, handler)
        gtk.StatusIcon.__init__(self)

        self.main_window = main_window
        self.menu = None
        self.tag = None # keeps the gobject id for the windows-hide-menu hack

        # message count icon
        self.unread_icon = None

        self.connect('activate', self._on_activate)
        self.connect('popup-menu', self._on_popup)

        self.set_login()
        gtk.StatusIcon.set_visible(self, True)

        self.set_tooltip("emesene")

    def set_login(self):
        """
        method called to set the state to the login window
        """
        self.menu = LoginMenu(self.handler, self.main_window)
        self.menu.show_all()
        if sys.platform == "win32":
            self.menu.connect('leave-notify-event', self.on_leave_notify_event)
            self.menu.connect('enter-notify-event', self.on_enter_notify_event)

        self.set_from_file(self.handler.theme.image_theme.logo_panel)

    def set_main(self, session):
        """
        method called to set the state to the main window
        """
        gui.BaseTray.set_main(self, session)
        if self.menu:
            self.menu.unsubscribe()
        self.menu = MainMenu(self.handler, self.main_window)
        self.menu.show_all()
        if sys.platform == "win32":
            self.menu.connect('leave-notify-event', self.on_leave_notify_event)
            self.menu.connect('enter-notify-event', self.on_enter_notify_event)

        self.set_tooltip("emesene - " + self.handler.session.account.account)
        self._on_status_change_succeed(self.handler.session.account.status)

    def windows_workaround(self, *args):
        if self.menu:
            self.menu.hide()

    def on_leave_notify_event(self, *args):
        """
        callback called when the mouse leaves this window
        """
        if self.tag is None:
            self.tag = gobject.timeout_add_seconds(1, self.windows_workaround)

    def on_enter_notify_event(self, *args):
        """
        callback called when the mouse enters this window
        """
        if self.tag:
            gobject.source_remove(self.tag)
            self.tag = None

    def _on_activate(self, trayicon):
        """
        callback called when the status icon is activated
        (includes clicking the icon)
        """
        if self.last_new_message is not None and (self.count != 0):
            # show the tab with the latest message
            cid = self.last_new_message
            conv_manager = self.handler.session.get_conversation_manager(cid)

            if conv_manager:
                conversation = conv_manager.has_similar_conversation(cid)
                conv_manager.present(conversation)
        else:
            self.handler.on_hide_show_mainwindow(self.main_window)

    def _on_status_change_succeed(self, stat):
        """
        change the icon in the tray according to user's state
        """
        if stat not in status.ALL or stat == -1:
            return

        if check_gtk3():
            self.unread_icon = self._get_numerable_icon_for_status(stat)
            self._update_numerable_icon(self.count)
        else:
            self.set_from_file(self.handler.theme.image_theme.status_icons_panel[stat])

    def count_changed(self, count):
        '''method called when unread message count changes'''
        if check_gtk3():
            self._update_numerable_icon(count)
        else:
            self.set_blinking((count != 0))

    def _get_numerable_icon_for_status(self, stat):
        '''create a new Numerable icon with current status as base image'''
        icon_path = self.handler.theme.image_theme.status_icons_panel[stat]
        gfile = Gio.File.new_for_path(icon_path)
        gicon = Gio.FileIcon.new(gfile)
        return gtk.NumerableIcon.new(gicon)

    def _update_numerable_icon(self, count):
        self.unread_icon.set_count(count)
        self.set_from_gicon(self.unread_icon)

    def _on_popup(self, trayicon, button, activate_time):
        """
        callback called when the popup of the status icon is activated
        (usually through right-clicking the status icon)
        """
        position = None
        user_data = None
        if os.name == 'mac' or sys.platform == 'linux2' or sys.platform == 'linux3':
            position = gtk.status_icon_position_menu
            user_data = trayicon
        self.menu.popup(None, None, position, button, activate_time, user_data)

    def _on_contact_attr_changed(self, *args):
        """
        This is called when a contact changes something
        """
        self.menu.list_contacts._on_contact_change_something(*args)

    def hide(self):
        self.unsubscribe()
        gtk.StatusIcon.set_visible(self, False)

    def unsubscribe(self):
        self.disconnect_signals()
        if self.menu:
            self.menu.unsubscribe()

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

    def unsubscribe(self):
        pass

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

        self.status = gtk.ImageMenuItem(_('Status'))
        self.status.set_image(gtk.image_new_from_stock(gtk.STOCK_CONVERT,
            gtk.ICON_SIZE_MENU))
        self.status_menu = StatusMenu.StatusMenu(handler.on_status_selected)
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
        self.preferences = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        self.preferences.connect('activate',
            lambda *args: self.handler.on_preferences_selected())

        self.unmute_label = _('Unmute sounds')
        self.unmute_stock = gtk.STOCK_MEDIA_PLAY
        self.mute_label = _('Mute sounds')
        self.mute_stock = gtk.STOCK_MEDIA_STOP
        self.mute = gtk.ImageMenuItem()
        self._on_b_mute_sounds_changed()
        self.handler.session.config.subscribe(self._on_b_mute_sounds_changed,
                                              'b_mute_sounds')
        self.mute.connect('activate', self._on_mute_unmute_sounds)

        self.append(self.hide_show_mainwindow)
        self.append(self.mute)
        if self.handler.session.session_has_service(e3.Session.SERVICE_STATUS):
            self.append(self.status)
        self.append(self.list)
        self.append(self.disconnect)
        self.append(self.preferences)
        self.append(gtk.SeparatorMenuItem())
        self.append(self.quit)

    def _on_mute_unmute_sounds(self, *args):
        ''' Toggle sound mute <-> unmute '''
        value = self.handler.session.config.b_mute_sounds
        self.handler.session.config.b_mute_sounds = not value

    def _on_b_mute_sounds_changed(self, *args):
        ''' Changes the menu item if b_mute_sounds changes '''
        if self.handler.session.config.b_mute_sounds:
            self.mute.set_label(self.unmute_label)
            self.mute.set_image(gtk.image_new_from_stock(self.unmute_stock,
                                gtk.ICON_SIZE_MENU))
        else:
            self.mute.set_label(self.mute_label)
            self.mute.set_image(gtk.image_new_from_stock(self.mute_stock,
                                gtk.ICON_SIZE_MENU))

    def unsubscribe(self):
        self.handler.session.config.unsubscribe(self._on_b_mute_sounds_changed,
                                              'b_mute_sounds')

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
        def strip_nick(contact1, contact2):
            return cmp(Plus.msnplus_strip(contact1.nick).lower(),
                       Plus.msnplus_strip(contact2.nick).lower())

        gtk.Menu.__init__(self)
        self.handler = handler
        self.main_window = main_window
        self.item_to_contacts = {}
        self.contacts_to_item = {}
        self.avatar_size = 20

        self.contactmanager = self.handler.session.contacts

        for contact in sorted(self.contactmanager.get_online_list(),
                              cmp = strip_nick):
            self.__append_contact(contact)

    def __append_contact(self, contact):
        """
        appends a contact to our submenu
        """
        item = gtk.ImageMenuItem()
        item.set_label(gui.Plus.msnplus_strip(contact.nick))
        pict = self.__get_contact_pixbuf_or_default(contact.picture)
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
        type_change = None
        if len(args) == 3:
            account, type_change, value_change = args
        elif len(args) == 4:
            account, type_change, value_change, do_notify = args
        elif len(args) == 2:
            account, filepath = args
            type_change = 'picture'

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
            if account in self.contacts_to_item:
                pict = self.__get_contact_pixbuf_or_default(filepath)
                self.contacts_to_item[account].set_image(pict)

    def _on_contact_clicked(self, menu_item):
        """
        called when contacts are clicked
        """
        acc = self.item_to_contacts[menu_item].account
        cid = time.time()
        self.main_window.content_main.on_new_conversation(cid, [acc], other_started=False)
        self.handler.session.new_conversation(acc, cid)

    def __get_contact_pixbuf_or_default(self, path):
        '''try to return a pixbuf of the user picture or the default
        picture
        '''
        pixbuf = utils.safe_gtk_pixbuf_load(
                        path, (self.avatar_size, self.avatar_size))
        if not pixbuf:
            pixbuf = utils.safe_gtk_pixbuf_load(
                        gui.theme.image_theme.user,
                        (self.avatar_size, self.avatar_size))
        picture = gtk.image_new_from_pixbuf(pixbuf)

        return picture
