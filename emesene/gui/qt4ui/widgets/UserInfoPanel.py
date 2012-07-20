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

'''This module contains the UserInfoPanel class.'''

import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore
from PyQt4.QtCore import Qt
from gui.qt4ui.Utils import tr

from gui import Plus
from gui.qt4ui import Utils


class UserInfoPanel (QtGui.QWidget):
    '''This class represents a label widget showing
    other contact's info in a conversation window'''
    # pylint: disable=W0612
    NAME = 'Header'
    DESCRIPTION = 'The widget used to to display contact\'s info in ' \
                  'the conversation widget'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''
    # pylint: enable=W0612

    def __init__(self, session, members, parent=None):
        '''Constructor'''
        QtGui.QWidget.__init__(self, parent)

        self.session = session
        self.members = members
        self._message_lbl = QtGui.QLabel()

        lay = QtGui.QHBoxLayout()
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._message_lbl)
        self.setLayout(lay)
        self._message_lbl.setTextFormat(Qt.RichText)
        # set context menu policy
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

        self._action_d = {}
        action_d = self._action_d
        self.menu = QtGui.QMenu(tr('Copy contact information'), self)

        action_d['nick_clipboard'] = QtGui.QAction(tr('Nickname'), self)
        action_d['nick_clipboard'].triggered.connect(
            self.on_copy_nick_to_clipboard)
        self.menu.addAction(action_d['nick_clipboard'])
        action_d['message_clipboard'] = QtGui.QAction(tr('Personal message'), self)
        action_d['message_clipboard'].triggered.connect(
            self.on_copy_message_to_clipboard)
        self.menu.addAction(action_d['message_clipboard'])
        action_d['account_clipboard'] = QtGui.QAction(tr('Email address'), self)
        action_d['account_clipboard'].triggered.connect(
            self.on_copy_account_to_clipboard)
        self.menu.addAction(action_d['account_clipboard'])

    def showContextMenu(self, point):
        self.menu.exec_(self.mapToGlobal(point))

    def on_copy_nick_to_clipboard(self, action):
        nick_list = []
        for member in self.members:
            contact = self.session.contacts.safe_get(member)
            nick_list.append(Plus.msnplus_strip(contact.nick))

        clipboard = QtGui.QApplication.clipboard()
        clipboard.setText(', '.join(nick_list))

    def on_copy_message_to_clipboard(self, action):
        pm_list = []
        for member in self.members:
            contact = self.session.contacts.safe_get(member)
            pm_list.append(Plus.msnplus_strip(contact.message))

        clipboard = QtGui.QApplication.clipboard()
        clipboard.setText(', '.join(pm_list))

    def on_copy_account_to_clipboard(self, action):
        mail_list = []
        for member in self.members:
            mail_list.append(member)

        clipboard = QtGui.QApplication.clipboard()
        clipboard.setText(', '.join(mail_list))

    def _set_information(self, lines):
        message, account = lines
        message = Utils.escape(message)
        message = Utils.parse_emotes(unicode(message))
        message = u'%s<br /><span style="font-size: small;">%s</span>' % (message, account)
        self._message_lbl.setText(message)

    def _get_information(self):
        '''return the text on the information'''
        return self._message_lbl.text()

    information = property(fget=_get_information, fset=_set_information)
