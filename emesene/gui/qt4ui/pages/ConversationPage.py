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

'''This module contains classes to represent the conversation page.'''

import logging
import e3

import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore

import gui
import extension
from gui.base import Plus

log = logging.getLogger('qt4ui.ConversationPage')


class ConversationPage (gui.base.ConversationManager, QtGui.QTabWidget):
    '''The Conversation Page'''
    NAME = 'MainPage'
    DESCRIPTION = 'The widget used to to display the conversation screen'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    def __init__(self, session, on_last_close, parent):
        '''Constructor'''
        gui.base.ConversationManager.__init__(self, session, on_last_close)
        QtGui.QTabWidget.__init__(self, parent)

        self.setTabsClosable(True)
        self.setDocumentMode(True)
        self.setTabPosition(self.session.config.get_or_set('i_tab_position', 0))
        # to prevent top level window's destruction:
        self.qt_parent = parent
        self.tabCloseRequested.connect(self._on_tab_close_request)
        self.session.config.subscribe(self._on_tab_position_changed,
            'i_tab_position')
        self.installEventFilter(EventFilter(self, self.focusInEvent))
        self.currentChanged.connect(self._on_switch_page)

    def _on_tab_position_changed(self, value):
        '''callback called when i_tab_position changes'''
        self.setTabPosition(value)

    def get_parent(self):
        '''Return a reference to the top level window containing this page'''
        return QtGui.QTabWidget.parent(self).parent()

    def set_current_page(self, tab_index):
        '''Show the chat tab at the given index'''
        QtGui.QTabWidget.setCurrentIndex(self, tab_index)

    #[START] -------------------- GUI.BASE.CONVERSATIONMANAGER_OVERRIDE

    def add_new_conversation(self, session, conv_id, members):
        '''Creates a new chat tab and returns it. This implements base's
        class abstract method.'''
        conversation_cls = extension.get_default('conversation')
        conversation = conversation_cls(session, conv_id, members)
        account = session.contacts.get(members[0])
        conversation.tab_index = self.addTab(conversation,
                    Plus.msnplus_strip(account.display_name))
        conversation.conv_manager = self
        return conversation

    def get_dimensions(self):
        '''
        Returns a tuple containing width, height, x coordinate, y coordinate
        '''
        size = self.size()
        position = self.pos()
        return size.width(), size.height(), position.x(), position.y()

    def hide_all(self):
        '''Hides the window'''
        # FIXME: shouldn't this be called on something else??
        self.get_parent().hide()

    def is_active(self):
        '''return True if the conversation manager is active'''
        return self.get_parent().hasFocus()

    def is_maximized(self):
        return self.get_parent().isMaximized()

    def present(self, conversation, b_single_window=False):
        '''Raises the tab containing the given conversation'''
        self.setCurrentIndex(conversation.tab_index)
        conversation.input.setFocus()

    def remove_conversation(self, conversation):
        '''Removes the chat tab. This implements base's class
        abstract method.'''
        index = self.indexOf(conversation)
        self.removeTab(index)

    def set_message_waiting(self, conversation, is_waiting):
        """
        inform the user that a message is waiting for the conversation
        """
        parent = self.get_parent()
        if parent is not None and conversation in self.conversations.values():
            current_index = self.currentIndex()
            if (not conversation.hasFocus() or current_index != conversation.tab_index):
                conversation.message_waiting = is_waiting

    def focusInEvent(self, widget):
        page = self.currentWidget()
        if page is not None:
            self.session.add_event(e3.Event.EVENT_MESSAGE_READ, page)
            self.set_message_waiting(page, False)

    def _on_switch_page(self, index):
        page = self.currentWidget()
        if page is not None:
            self.session.add_event(e3.Event.EVENT_MESSAGE_READ, page)
            self.set_message_waiting(page, False)
            page.input_grab_focus()

    #[START] -------------------- GUI.BASE.CONVERSATIONMANAGER_OVERRIDE
    def _on_tab_close_request(self, index):
        '''Slot executed when the use clicks the close button in a tab'''
        self.close(self.widget(index))


class EventFilter(QtCore.QObject):
    def __init__(self, parent=None, callback=None):
        QtCore.QObject.__init__(self, parent)
        self.callback = callback
        self.widget = parent

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.WindowActivate:
            if self.parent().isActiveWindow():
                self.callback(self.widget)
        return QtCore.QObject.eventFilter(self, obj, event)
