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


''' This module contains the top level window class '''

import logging

import PyQt4.QtGui as QtGui
from PyQt4.QtCore import Qt

import extension
import gui

log = logging.getLogger('qt4ui.TopLevelWindow')


class TopLevelWindow (QtGui.QMainWindow):
    ''' Class representing the main window '''
    # pylint: disable=W0612
    NAME = 'TopLevelWindow'
    DESCRIPTION = 'The window used to contain all the _content of emesene'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''
    # pylint: enable=W0612

    def __init__(self, cb_on_close):
        log.debug('Creating a new main window!')
        QtGui.QMainWindow.__init__(self)
        self._content_type = 'empty'
        self._cb_on_close = cb_on_close
        self._given_cb_on_close = cb_on_close
        self._content = None
        self._content_conv = None

        self.setObjectName('mainwindow')
        self.setWindowIcon(QtGui.QIcon(gui.theme.image_theme.logo))
        self._page_stack = QtGui.QStackedWidget()
        self.setCentralWidget(self._page_stack)

    def __del__(self):
        log.debug('adieu TLW!!!')

    def _get_content_conv(self):
        '''content getter'''
        return self._content_conv

    def _set_content_conv(self, content_conv):
        '''content setter'''
        if self._content_conv:
            del self._content_conv
        self._content_conv = content_conv

    content_conv = property(_get_content_conv, _set_content_conv)

    def clear(self): #emesene's
        '''remove the content from the main window'''
        pass

    def iconify(self):
        '''Iconifies the window'''
        self.setWindowState(Qt.WindowMinimized)

    def present(self, b_single_window=False): # emesene's
        '''(Tries to) raise the window'''
        QtGui.QMainWindow.activateWindow(self)

    def set_location(self, width, height, posx, posy, single_window=False): #emesene's
        '''Sets size and position on screen '''
        #FIXME: single window
        self.resize(width, height)
        self.move(posx, posy)

    def get_dimensions(self): #emesene's
        '''
        Returns a tuple containing width, height, x coordinate, y coordinate
        '''
        size = self.size()
        position = self.pos()
        return size.width(), size.height(), position.x(), position.y()

    def go_connect(self, on_cancel_login, avatar_path, config):
        '''Adds a 'connecting' page to the top level window and shows it'''
        log.debug('GO CONNECT! ^_^')
        connecting_window_cls = extension.get_default('connecting window')
        connecting_page = connecting_window_cls(on_cancel_login,
                                                avatar_path, config)
        self._content_type = 'connecting'
        self._switch_to_page(connecting_page)
        self.menuBar().hide()

    def go_conversation(self, session, on_close):
        '''Adds a conversation page to the top level window and shows it'''
        conversation_window_cls = extension.get_default('conversation window')
        conversation_page = conversation_window_cls(session,
                            on_last_close=self._on_last_tab_close, parent=self)
        self._content_type = 'conversation'
        self.content_conv = conversation_page
        self._switch_to_page(conversation_page)
        self.menuBar().hide()

    # TODO: don't reinstantiate existing pages, or don't preserve old pages.
    def go_login(self, callback, on_preferences_changed, config=None,
                 config_dir=None, config_path=None, proxy=None,
                 use_http=None, use_ipv6=None,
                 session_id=None, cancel_clicked=False, no_autologin=False):
               #emesene's
        # pylint: disable=R0913
        '''Adds a login page to the top level window and shows it'''
        login_window_cls = extension.get_default('login window')
        login_page = login_window_cls(callback, on_preferences_changed, config,
                                      config_dir, config_path, proxy,
                                      use_http, use_ipv6,
                                      session_id, cancel_clicked, no_autologin)
        self._content_type = 'login'
        if not login_page.autologin_started:
            self._switch_to_page(login_page)
        self.setMenuBar(None)

    def go_main(self, session, on_new_conversation, quit_on_close=False):
        '''Adds a main page (the one with the contact list) to the top
        level window and shows it'''
        log.debug('GO MAIN! ^_^')
        # TODO: handle quit_on_close (??) [consider creating a base class and
        # moving code there.]
        main_window_cls = extension.get_default('main window')
        main_page = main_window_cls(session, on_new_conversation, self.setMenuBar)
        self._content_type = 'main'
        self._switch_to_page(main_page)
        self._setup_main_menu(session, main_page.contact_list)

        if quit_on_close:
            self._cb_on_close = self._given_cb_on_close
        else:
            self._cb_on_close = lambda *args: self.hide()

    def is_maximized(self):
        '''Checks wether the window is maximized'''
        return QtGui.QMainWindow.isMaximized(self)

    def maximize(self):
        '''Tries to maximize the window'''
        QtGui.QMainWindow.showMaximized(self)

    def on_disconnect(self, cb_on_close):
        '''called when the user is disconnected'''
        self.content.unsubscribe_signals()
        self._cb_on_close = cb_on_close

    def _get_content(self):
        '''Getter method for propery "content"'''
        log.debug('Getting \'content\'')
        return self._content

    content = property(_get_content)

    def _get_content_type(self):
        ''' Getter method for "content_type" property'''
        return self._content_type

    content_type = property(_get_content_type)

    def _on_last_tab_close(self):
        '''Slot called when the user closes the last tab in
        a conversation window'''
        self._cb_on_close(self._content)
        self.hide()

    def _setup_main_menu(self, session, contact_list):
        '''build all the menus used on the client'''
        menu_hnd = gui.base.MenuHandler(session, contact_list)
        main_menu_cls = extension.get_default('main menu')
        menu = main_menu_cls(menu_hnd, session)
        self.setMenuBar(menu)

    def _switch_to_page(self, page_widget):
        ''' Shows the given page '''
        index = self._page_stack.indexOf(page_widget)
        if index == -1:
            index = self._page_stack.addWidget(page_widget)
        self._page_stack.setCurrentIndex(index)
        self._content = page_widget

# -------------------- QT_OVERRIDE

    def closeEvent(self, event):
        # pylint: disable=C0103
        ''' Overrides QMainWindow's close event '''
        log.debug('TopLevelWindow\'s close event: %s, %s' % (
                                    self.content, str(self._cb_on_close)))
        cb_result = self._cb_on_close(self._content)
        if (cb_result is None) or (cb_result is True):
            event.ignore()
        # FIXME: dirty HACK. when we close the conversation window,
        # self._cb_on_close closes each conversation tab without checking
        # if it isclosing the last tab, so _on_last_tab_close doesn't get
        #called and the conversation window remains opened and empty.
        if str(self._cb_on_close).find(
                'Controller._on_conversation_window_close') > -1:
            self.hide()

