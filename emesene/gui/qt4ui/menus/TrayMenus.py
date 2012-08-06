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

'''This module contains menu widgets' classes'''

import PyQt4.QtGui      as QtGui

from gui.qt4ui.Utils import tr
import time
import os

import extension
import e3
import gui
from gui import Plus

ICON = QtGui.QIcon.fromTheme


class TrayMainMenu (QtGui.QMenu):
    '''Tray's context menu, shown when main window is shown'''
    NAME = 'Tray Main Menu'
    DESCRIPTION = 'The Main Menu of the tray icon'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    def __init__(self, handler, main_window, parent=None):
        '''Constructor'''
        QtGui.QMenu.__init__(self, 'emesene2', parent)

        self._handler = handler

        status_menu_cls = extension.get_default('menu status')

        self.hide_show_mainwindow = QtGui.QAction(tr('Hide/Show emesene'), self)
        self.status_menu = status_menu_cls(handler.on_status_selected)
        self.list = ContactsMenu(handler, main_window)
        self.disconnect = QtGui.QAction(ICON('network-disconnect'),
                                        tr('Disconnect'), self)
        self.quit = QtGui.QAction(ICON('application-exit'),
                                 tr('Quit'), self)
        self.preferences = QtGui.QAction(ICON('document-properties'),
                                 tr('Preferences'), self)

        self.unmute_label = tr('Unmute sounds')
        self.unmute_stock = ICON('media-playback-start')
        self.mute_label = tr('Mute sounds')
        self.mute_stock = ICON('media-playback-stop')
        self.mute = QtGui.QAction(self.mute_stock, self.mute_label, self)
        self._on_b_mute_sounds_changed()
        self._handler.session.config.subscribe(self._on_b_mute_sounds_changed,
                                              'b_mute_sounds')
        self.addAction(self.hide_show_mainwindow)
        self.addAction(self.mute)
        if self._handler.session.session_has_service(e3.Session.SERVICE_STATUS):
            self.addMenu(self.status_menu)
        self.addMenu(self.list)
        self.addAction(self.disconnect)
        self.addAction(self.preferences)
        self.addSeparator()
        self.addAction(self.quit)

        self.disconnect.triggered.connect(
            lambda *args: self._handler.on_disconnect_selected())
        self.quit.triggered.connect(
            lambda *args: self._handler.on_quit_selected())
        self.preferences.triggered.connect(
            lambda *args: self._handler.on_preferences_selected())
        self.mute.triggered.connect(self._on_mute_unmute_sounds)

    def _on_mute_unmute_sounds(self, *args):
        ''' Toggle sound mute <-> unmute '''
        value = self._handler.session.config.b_mute_sounds
        self._handler.session.config.b_mute_sounds = not value

    def _on_b_mute_sounds_changed(self, *args):
        ''' Changes the menu item if b_mute_sounds changes '''
        if self._handler.session.config.b_mute_sounds:
            self.mute.setText(self.unmute_label)
            self.mute.setIcon(self.unmute_stock)
        else:
            self.mute.setText(self.mute_label)
            self.mute.setIcon(self.mute_stock)

    def unsubscribe(self):
        self._handler.session.config.unsubscribe(self._on_b_mute_sounds_changed,
                                              'b_mute_sounds')


class TrayLoginMenu (QtGui.QMenu):
    '''a widget that represents the menu displayed
    on the trayicon on the login window'''

    def __init__(self, handler, main_window, parent=None):
        '''
        constructor

        handler -- a e3common.Handler.TrayIconHandler object
        '''
        QtGui.QMenu.__init__(self, parent)
        self._handler = handler
        self.hide_show_mainwindow = QtGui.QAction(tr('Hide/Show emesene'), self)
        self.quit = QtGui.QAction(ICON('application-exit'), tr('Quit'), self)

        self.addAction(self.hide_show_mainwindow)
        self.addAction(self.quit)

        self.quit.triggered.connect(
            lambda *args: self._handler.on_quit_selected())
        self.hide_show_mainwindow.triggered.connect(
            lambda *args: self.handler.on_hide_show_mainwindow(main_window))

    def unsubscribe(self):
        pass


class ContactsMenu(QtGui.QMenu):
    """
    a gtk menu that contains session's contacts
    """
    NAME = 'Contacts Menu'
    DESCRIPTION = tr('A menu with sessions\' contacts')
    AUTHOR = 'Riccardo (C10uD)'
    WEBSITE = 'www.emesene.org'

    def __init__(self, handler, main_window=None, parent=None):
        """
        constructor
        """
        def strip_nick(contact1, contact2):
            return cmp(Plus.msnplus_strip(contact1.nick).lower(),
                       Plus.msnplus_strip(contact2.nick).lower())

        QtGui.QMenu.__init__(self, tr("Contacts"), parent)
        self.handler = handler
        self.main_window = main_window
        self.item_to_contacts = {}
        self.contacts_to_item = {}
        self.avatar_size = 20

        self.contactmanager = self.handler.session.contacts

        for contact in sorted(self.contactmanager.get_online_list(),
                              cmp=strip_nick):
            self.__append_contact(contact)
        self.triggered.connect(self._on_contact_clicked)

    def __append_contact(self, contact):
        """
        appends a contact to our submenu
        """
        item = QtGui.QAction(Plus.msnplus_strip(contact.nick), self)
        pict = self.__get_contact_pixbuf_or_default(contact.picture)
        item.setIcon(QtGui.QIcon(pict))
        self.item_to_contacts[item] = contact
        self.contacts_to_item[contact.account] = item

        self.addAction(item)

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
            else:  # offline
                if account in self.contacts_to_item:
                    self.removeAction(self.contacts_to_item[account])
                    del self.item_to_contacts[self.contacts_to_item[account]]
                    del self.contacts_to_item[account]

        if type_change == 'nick':
            if account in self.contacts_to_item:
                nick = self.item_to_contacts[self.contacts_to_item[account]].nick
                self.contacts_to_item[account].setText(nick)

        if type_change == 'picture':
            if account in self.contacts_to_item:
                pict = self.__get_contact_pixbuf_or_default(filepath)
                self.contacts_to_item[account].setIcon(QtGui.QIcon(pict))

    def _on_contact_clicked(self, menu_item):
        """
        called when contacts are clicked
        """
        acc = self.item_to_contacts[menu_item].account
        cid = time.time()
        self.main_window.content.on_new_conversation(cid, [acc], other_started=False)
        self.handler.session.new_conversation(acc, cid)

    def __get_contact_pixbuf_or_default(self, filename):
        '''try to return a pixbuf of the user picture or the default
        picture
        '''
        if filename and not os.path.exists(filename):
            return filename
        else:
            return gui.theme.image_theme.user
