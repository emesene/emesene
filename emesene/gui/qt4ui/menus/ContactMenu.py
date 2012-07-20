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

import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore
from gui.qt4ui.Utils import tr

import gui
import e3
from gui.base import Plus

ICON = QtGui.QIcon.fromTheme

class ContactMenu(QtGui.QMenu):
    '''A class that represents a menu to handle contact related information'''
    NAME = 'Contact Menu'
    DESCRIPTION = 'The menu that displays contact options'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    def __init__(self, handler, session, parent=None):
        '''
        constructor

        handler -- a e3common.Handler.ContactHandler
        '''
        QtGui.QMenu.__init__(self, tr('Contact'), parent)
        self._handler = handler
        self.session = session

        self._action_d = {}
        action_d = self._action_d
        action_d['add'] = QtGui.QAction(ICON('list-add'), tr('Add'), self)
        action_d['add'].triggered.connect(
            lambda *args: self._handler.on_add_contact_selected())
        action_d['remove'] = QtGui.QAction(ICON('list-remove'), tr('Remove'), self)
        action_d['remove'].triggered.connect(
            lambda *args: self._handler.on_remove_contact_selected())
        action_d['block'] = QtGui.QAction(ICON('dialog-cancel'), tr('Block'), self)
        action_d['block'].triggered.connect(
            lambda *args: self._handler.on_block_contact_selected())
        action_d['unblock'] = QtGui.QAction(ICON('dialog-ok-apply'),
                                       tr('Unblock'), self)
        action_d['unblock'].triggered.connect(
            lambda *args: self._handler.on_unblock_contact_selected())
        action_d['set_alias'] = QtGui.QAction(tr('Set alias'), self)
        action_d['set_alias'].triggered.connect(
            lambda *args: self._handler.on_set_alias_contact_selected())

        action_d['move_to'] = QtGui.QMenu(tr('Move to group'), self)
        action_d['copy_to'] = QtGui.QMenu(tr('Copy to group'), self)
        action_d['remove_from'] = QtGui.QMenu(tr('Remove from group'), self)

        action_d['view_info'] = QtGui.QAction(tr('View information'), self)
        action_d['view_info'].triggered.connect(
            lambda *args: self._handler.on_view_information_selected())

        action_d['copy_info'] = QtGui.QMenu(tr('Copy contact information'), self)

        action_d['nick_clipboard'] = QtGui.QAction(tr('Nickname'), self)
        action_d['copy_info'].addAction(action_d['nick_clipboard'])
        action_d['nick_clipboard'].triggered.connect(
            self.on_copy_nick_to_clipboard)
        action_d['message_clipboard'] = QtGui.QAction(tr('Personal message'), self)
        action_d['message_clipboard'].triggered.connect(
            self.on_copy_message_to_clipboard)
        action_d['copy_info'].addAction(action_d['message_clipboard'])
        action_d['account_clipboard'] = QtGui.QAction(tr('Email address'), self)
        action_d['account_clipboard'].triggered.connect(
            self.on_copy_account_to_clipboard)
        action_d['copy_info'].addAction(action_d['account_clipboard'])

        if self.session.session_has_service(e3.Session.SERVICE_CONTACT_MANAGING):
            self.addAction(action_d['add'])
        if self.session.session_has_service(e3.Session.SERVICE_CONTACT_BLOCK):
            self.addAction(action_d['block'])
            self.addAction(action_d['unblock'])
        if self.session.session_has_service(e3.Session.SERVICE_CONTACT_MANAGING):
            self.addAction(action_d['remove'])
            self.addSeparator()
        if self.session.session_has_service(e3.Session.SERVICE_CONTACT_ALIAS):
            self.addAction(action_d['set_alias'])
        self.addAction(action_d['view_info'])
        self.addSeparator()
        if self.session.session_has_service(e3.Session.SERVICE_GROUP_MANAGING):
            self.addMenu(action_d['move_to'])
            self.addMenu(action_d['copy_to'])
            self.addMenu(action_d['remove_from'])
            self.addSeparator()
        self.addMenu(action_d['copy_info'])
        self.setIcon(QtGui.QIcon(gui.theme.image_theme.user))

        self.set_unblocked()

        self.aboutToShow.connect(
            lambda *args: self._update_groups())

    def on_copy_account_to_clipboard(self, action):
        contact = self._handler.contact_list.get_contact_selected()
        if contact:
            clipboard = QtGui.QApplication.clipboard()
            clipboard.setText(contact.account)

    def on_copy_nick_to_clipboard(self, action):
        contact = self._handler.contact_list.get_contact_selected()
        if contact:
            clipboard = QtGui.QApplication.clipboard()
            clipboard.setText(Plus.msnplus_strip(contact.nick))

    def on_copy_message_to_clipboard(self, action):
        contact = self._handler.contact_list.get_contact_selected()
        if contact:
            clipboard = QtGui.QApplication.clipboard()
            clipboard.setText(Plus.msnplus_strip(contact.message))

    def _update_groups(self):
        '''Updates the three submenus whenever ContactMenu is shown'''
        handler = self._handler
        move_to = self._action_d['move_to']
        copy_to = self._action_d['copy_to']
        remove_from = self._action_d['remove_from']

        move_to.clear()
        copy_to.clear()
        remove_from.clear()

        groups_d = handler.get_all_groups()
        contact_groups_uids = handler.get_contact_groups()
        # dirty hack:
        if handler.is_by_group_view() and \
           handler.contact_list.get_contact_selected() is not None:
            for uid, group in groups_d.iteritems():
                if uid not in contact_groups_uids:
                    action1 = QtGui.QAction(unicode(group.name), self)
                    action2 = QtGui.QAction(unicode(group.name), self)
                    action1.setData(group)
                    action2.setData(group)
                    move_to.addAction(action1)
                    copy_to.addAction(action2)
                    move_to.triggered.connect(self._on_move_to_group)
                    copy_to.triggered.connect(self._on_copy_to_group)
                else:
                    action = QtGui.QAction(unicode(group.name), self)
                    action.triggered.connect(
                        lambda *args: handler.on_remove_from_group_selected(group))
                    remove_from.addAction(action)

        # Deactivate the submenus if they're empty:
        move_to.setEnabled(not move_to.isEmpty())
        copy_to.setEnabled(not copy_to.isEmpty())
        remove_from.setEnabled(not remove_from.isEmpty())

    def _on_move_to_group(self, action):
        group = action.data().toPyObject()
        self._handler.on_move_to_group_selected(group)

    def _on_copy_to_group(self, action):
        group = action.data().toPyObject()
        self._handler.on_copy_to_group_selected(group)

    def _on_remove_from_group(self, action):
        group = action.data().toPyObject()
        self._handler.on_remove_from_group_selected(group)

    def set_blocked(self):
        self._action_d['block'].setVisible(False)
        self._action_d['unblock'].setVisible(True)

    def set_unblocked(self):
        self._action_d['unblock'].setVisible(False)
        self._action_d['block'].setVisible(True)
