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

from e3.common import MessageFormatter
import gui
from gui.base import Plus
from gui.base import Desktop
log = logging.getLogger('qt4ui.widgets.ChatOutput')


class ChatOutput (gui.base.OutputText, QtGui.QTextBrowser):
    '''A widget which displays various messages of a conversation'''
    NAME = 'Output Text'
    DESCRIPTION = _('A widget to display the conversation messages')
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    search_request = QtCore.pyqtSignal(basestring)

    def __init__(self, config, parent=None):
        '''Constructor'''
        QtGui.QTextBrowser.__init__(self, parent)
        gui.base.OutputText.__init__(self, config)
        self.formatter = MessageFormatter()
        self._chat_text = QtCore.QString('')
        self.setOpenLinks(False)
        self.anchorClicked.connect(self._on_link_clicked)
        self.clear()

    def _on_link_clicked(self, url):
        href = unicode(url.toString())
        if href.startswith("search://"):
            self.search_request.emit(href)
            return

        if not href.startswith("file://"):
            Desktop.open(href)
            return

    def clear(self, source="", target="", target_display="",
            source_img="", target_img=""):
        '''clear the content'''
        QtGui.QTextBrowser.clear(self)
        self._chat_text = QtCore.QString('')
        gui.base.OutputText.clear(self)

    def add_message(self, msg, scroll):
        if msg.type == "status":
            msg.message = Plus.msnplus_strip(msg.message)
            text = self.formatter.format_information(msg.message)
        else:
            msg.alias = Plus.msnplus_strip(msg.alias)
            msg.display_name = Plus.msnplus_strip(msg.display_name)
            text = self.formatter.format(msg)
        self._append_to_chat(text, scroll)

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
