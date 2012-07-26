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

'''This module contains the ChatTextEdit class'''

import logging

import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore

import e3
from gui.base import Plus

log = logging.getLogger('qt4ui.widgets.ChatOutput')


class ChatOutput (QtGui.QTextBrowser):
    '''A widget which displays various messages of a conversation'''
    NAME = 'Output Text'
    DESCRIPTION = _('A widget to display the conversation messages')
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    def __init__(self, config, parent=None):
        '''Constructor'''
        QtGui.QTextBrowser.__init__(self, parent)
        self._chat_text = QtCore.QString('')
        self.config = config
        self.locked = 0
        self.pending = []

    def clear(self, source="", target="", target_display="",
            source_img="", target_img=""):
        '''clear the content'''
        QtGui.QTextBrowser.clear(self)

    def lock(self):
        self.locked += 1

    def unlock(self):
        #add messages and then unlock
        self.locked -= 1
        if self.locked <= 0:
            for text in self.pending:
                self._append_to_chat(text, self.config.b_allow_auto_scroll)
            self.pending = []
            self.locked = 0

    def append(self, text, msg, scroll=True):
        '''append formatted text to the widget'''
        if self.locked and msg.type != e3.Message.TYPE_OLDMSG:
            self.pending.append(text)
        else:
            self._append_to_chat(text, scroll)

    def send_message(self, formatter, msg):
        '''add a message to the widget'''
        msg.alias = Plus.msnplus_strip(msg.alias)
        msg.display_name = Plus.msnplus_strip(msg.display_name)

        text = formatter.format(msg)
        self.append(text, msg, self.config.b_allow_auto_scroll)

    def receive_message(self, formatter, msg):
        '''add a message to the widget'''
        msg.alias = Plus.msnplus_strip(msg.alias)
        msg.display_name = Plus.msnplus_strip(msg.display_name)

        text = formatter.format(msg)
        self.append(text, msg, self.config.b_allow_auto_scroll)

    def information(self, formatter, msg):
        '''add an information message to the widget'''
        msg.message = Plus.msnplus_strip(msg.message)
        text = formatter.format_information(msg.message)
        self.append(text, msg, self.config.b_allow_auto_scroll)

    def _append_to_chat(self, html_string, scroll):
        '''Method that appends an html string to the chat view'''
        vert_scroll_bar = self.verticalScrollBar()
        position = vert_scroll_bar.value()
        self._chat_text.append(html_string)
        self.setText(self._chat_text)

        if scroll:
            vert_scroll_bar.setValue(vert_scroll_bar.maximum())
        else:
            vert_scroll_bar.setValue(position)

    def update_p2p(self, account, _type, *what):
        ''' new p2p data has been received (custom emoticons) '''
        #FIXME:
        pass
