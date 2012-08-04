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
import extension

ICON = QtGui.QIcon.fromTheme


class MainMenu(QtGui.QMenuBar):
    '''A widget that represents the main menu of the main window'''
    NAME = 'Main Menu'
    DESCRIPTION = 'The Main Menu of the main window'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    def __init__(self, handlers, session, parent=None):
        '''Constructor'''
        QtGui.QMenuBar.__init__(self, parent)

        self._handlers = handlers
        self.session = session

        file_menu_cls = extension.get_default('menu file')
        actions_menu_cls = extension.get_default('menu actions')
        options_menu_cls = extension.get_default('menu options')
        help_menu_cls = extension.get_default('menu help')

        self.file_menu = file_menu_cls(self._handlers.file_handler)
        self.actions_menu = actions_menu_cls(self._handlers.actions_handler,
                                                session)
        self.options_menu = options_menu_cls(self._handlers.options_handler,
                                             session.config)
        self.help_menu = help_menu_cls(self._handlers.help_handler)

        self.addMenu(self.file_menu)
        self.addMenu(self.actions_menu)
        self.addMenu(self.options_menu)
        self.addMenu(self.help_menu)


class FileMenu(QtGui.QMenu):
    '''A widget that represents the File popup menu located on the main menu'''

    def __init__(self, handler, parent=None):
        '''
        constructor

        handler -- e3common.Handler.FileHandler
        '''
        QtGui.QMenu.__init__(self, tr('File'), parent)
        self._handler = handler
        status_menu_cls = extension.get_default('menu status')

        self.status_menu = status_menu_cls(handler.on_status_selected)
        disconnect_action = QtGui.QAction(ICON('network-disconnect'),
                                          tr('Disconnect'), self)
        quit_action = QtGui.QAction(ICON('application-exit'), tr('Quit'), self)

        self.addMenu(self.status_menu)
        self.addAction(disconnect_action)
        self.addSeparator()
        self.addAction(quit_action)

        disconnect_action.triggered.connect(
                        lambda *args: self._handler.on_disconnect_selected())
        quit_action.triggered.connect(
                        lambda *args: self._handler.on_quit_selected())


class ActionsMenu(QtGui.QMenu):
    '''A widget that represents the Actions
    popup menu located on the main menu'''

    def __init__(self, handler, session, parent=None):
        '''
        constructor

        handler -- e3common.Handler.ActionsHandler
        '''
        QtGui.QMenu.__init__(self, tr('Actions'), parent)
        self._handler = handler

        contacts_menu_cls = extension.get_default('menu contact')
        group_menu_cls = extension.get_default('menu group')
        profile_menu_cls = extension.get_default('menu profile')

        self.contact_menu = contacts_menu_cls(self._handler.contact_handler,
                                                session)
        self.group_menu = group_menu_cls(self._handler.group_handler)
        self.my_profile_menu = profile_menu_cls(
                                            self._handler.my_account_handler)
        self.addMenu(self.contact_menu)
        self.addMenu(self.group_menu)
        self.addMenu(self.my_profile_menu)


class OptionsMenu(QtGui.QMenu):
    '''A widget that represents the Options
    popup menu located on the main menu'''

    def __init__(self, handler, config, parent=None):
        '''
        constructor

        handler -- e3common.Handler.OptionsHandler
        '''
        QtGui.QMenu.__init__(self, tr('Options'), parent)
        self.handler = handler

        # "Show" submenu
        self.show_menu = QtGui.QMenu(tr('Show...'))

        show_offline = QtGui.QAction(tr('Show offline contacts'), self)
        show_empty_groups = QtGui.QAction(tr('Show empty groups'), self)
        show_blocked = QtGui.QAction(tr('Show blocked contacts'), self)

        show_offline.setCheckable(True)
        show_empty_groups.setCheckable(True)
        show_blocked.setCheckable(True)
        show_offline.setChecked(config.b_show_offline)
        show_empty_groups.setChecked(config.b_show_empty_groups)
        show_blocked.setChecked(config.b_show_blocked)

        self.show_menu.addAction(show_offline)
        self.show_menu.addAction(show_empty_groups)
        self.show_menu.addAction(show_blocked)

        show_offline.triggered.connect(
                            self.handler.on_show_offline_toggled)
        show_empty_groups.triggered.connect(
                            self.handler.on_show_empty_groups_toggled)
        show_blocked.triggered.connect(
                            self.handler.on_show_blocked_toggled)
        # ----

        order_action_group = QtGui.QActionGroup(self)
        by_status = QtGui.QAction(tr('Order by status'), self)
        by_group = QtGui.QAction(tr('Order by group'), self)
        group_offline = QtGui.QAction(tr('Group offline contacts'), self)
        preferences = QtGui.QAction(ICON('preferences-other'),
                                    tr('Preferences...'), self)

        self.addAction(by_status)
        self.addAction(by_group)
        self.addSeparator()
        self.addMenu(self.show_menu)
        self.addAction(group_offline)
        self.addSeparator()
        self.addAction(preferences)

        order_action_group.addAction(by_status)
        order_action_group.addAction(by_group)
        by_group.setCheckable(True)
        by_status.setCheckable(True)
        group_offline.setCheckable(True)
        by_group.setChecked(config.b_order_by_group)
        by_status.setChecked(not config.b_order_by_group)
        group_offline.setChecked(config.b_group_offline)

        by_group.triggered.connect(
                            self.handler.on_order_by_group_toggled)
        group_offline.triggered.connect(
                            self.handler.on_group_offline_toggled)
        preferences.triggered.connect(
            lambda *args: self.handler.on_preferences_selected())
        by_status.toggled.connect(
                            self.handler.on_order_by_status_toggled)


class HelpMenu(QtGui.QMenu):
    '''A widget that represents the Help popup menu located on the main menu'''

    def __init__(self, handler, parent=None):
        '''
        constructor

        handler -- e3common.Handler.HelpHandler
        '''
        QtGui.QMenu.__init__(self, tr('Help'), parent)
        self.handler = handler

        self.website = QtGui.QAction(tr('Website'), self)
        self.about = QtGui.QAction(tr('About'), self)
        self.debug = QtGui.QAction(tr('Debug'), self)
        self.updatecheck = QtGui.QAction(tr('Check for updates'), self)

        self.addAction(self.website)
        self.addAction(self.about)
        self.addAction(self.debug)
        self.addSeparator()
        self.addAction(self.updatecheck)

        self.website.triggered.connect(
            lambda *args: self.handler.on_website_selected())
        self.about.triggered.connect(
            lambda *args: self.handler.on_about_selected())
        self.debug.triggered.connect(
            lambda *args: self.handler.on_debug_selected())
        self.updatecheck.triggered.connect(
            lambda *args: self.handler.on_check_update_selected())
