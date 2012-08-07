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

''' This module contains the tray icon's class'''

import sys
import PyQt4.QtGui as QtGui

import gui
import extension
from e3 import status


class TrayIcon (QtGui.QSystemTrayIcon, gui.BaseTray):
    '''A class that implements the tray icon of emesene for Qt4'''
    NAME = 'TrayIcon'
    DESCRIPTION = 'Qt4 Tray Icon'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    def __init__(self, handler, main_window=None):
        '''
        constructor

        handler -- a e3common.Handler.TrayIconHandler object
        '''
        gui.BaseTray.__init__(self, handler)
        QtGui.QSystemTrayIcon.__init__(self)

        self._main_window = main_window
        self.menu = None
        self._conversations = None

        self.setIcon(QtGui.QIcon(gui.theme.image_theme.logo))
        self.activated.connect(self._on_tray_icon_clicked)

        self.set_login()

        # TODO: this is for mac os, and should be changed in the
        # future (probably no tray icon at all, just the dock icon)
        if sys.platform == 'darwin':
            icon = QtGui.QIcon(gui.theme.image_theme.logo)
            qt_app = QtGui.QApplication.instance()
            qt_app.setWindowIcon(icon)
            qt_app.setApplicationName('BHAWH')
        else:
            self.show()

    def set_login(self):
        '''Called when the login window is shown. Sets a proper
        context menu in the Tray Icon.'''
        tray_login_menu_cls = extension.get_default('tray login menu')
        self.menu = tray_login_menu_cls(self.handler, self._main_window)
        self.setIcon(QtGui.QIcon(gui.theme.image_theme.logo_panel))
        self.setToolTip("emesene")
        if sys.platform == 'darwin':
            QtGui.qt_mac_set_dock_menu(self.menu)
        else:
            self.setContextMenu(self.menu)

    def set_main(self, session):
        '''Called when the main window is shown. Stores the contact list
        and registers the callback for the status_change_succeed event'''
        gui.BaseTray.set_main(self, session)
        if self.menu:
            self.menu.unsubscribe()
        tray_main_menu_cls = extension.get_default('tray main menu')
        self.menu = tray_main_menu_cls(self.handler, self._main_window)
        self.setToolTip("emesene - " + self.handler.session.account.account)
        self._on_status_change_succeed(self.handler.session.account.status)
        if sys.platform == 'darwin':
            QtGui.qt_mac_set_dock_menu(self.menu)
        else:
            self.setContextMenu(self.menu)

    def set_conversations(self, conversations):
        '''Store a reference to the conversation page'''
        self._conversations = conversations

    def set_visible(self, visible):
        '''Changes icon's visibility'''
        self.setVisible(visible)

    def _on_tray_icon_clicked(self, reason):
        '''This slot is called when the user clicks the tray icon.
        Toggles main window's visibility'''

        if not self._main_window:
            return

        if reason == QtGui.QSystemTrayIcon.Trigger:
            if not self._main_window.isVisible():
                self._main_window.show()
                self._main_window.activateWindow()
                self._main_window.raise_()
            else:  # visible
                if self._main_window.isActiveWindow():
                    self._main_window.hide()
                else:
                    self._main_window.activateWindow()
                    self._main_window.raise_()
        elif reason == QtGui.QSystemTrayIcon.Context:
            if self.menu:
                self.menu.show()

    def _on_contact_attr_changed(self, *args):
        """
        This is called when a contact changes something
        """
        self.menu.list._on_contact_change_something(*args)

    def _on_status_change_succeed(self, stat):
        """
        This is called when status is successfully changed
        """
        if stat not in status.ALL or stat == -1:
            return
        self.setIcon(QtGui.QIcon(
                            gui.theme.image_theme.status_icons_panel[stat]))

    def hide(self):
        self.unsubscribe()
        QtGui.QSystemTrayIcon.setVisible(self, False)

    def unsubscribe(self):
        self.disconnect_signals()
        if self.menu:
            self.menu.unsubscribe()
