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
'''This module contains the ContactList class'''

import logging

import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore

import extension
import gui

from gui.qt4ui.widgets import ContactListDelegate
from gui.qt4ui.widgets import ContactListModel
from gui.qt4ui.widgets import ContactListProxy
from gui.qt4ui.widgets.ContactListModel import Role


log = logging.getLogger('qt4ui.widgets.ContactList')

class ContactList (gui.ContactList, QtGui.QTreeView):
    '''A Contactlist Widget'''
    # pylint: disable=W0612
    NAME = 'MainPage'
    DESCRIPTION = 'The widget used to to display the contact list'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''
    # pylint: enable=W0612

    new_conversation_requested = QtCore.pyqtSignal(basestring)

    def __init__(self, session, parent=None):
        QtGui.QTreeView.__init__(self, parent)
        dialog = extension.get_default('dialog')
        # We need a model *before* callig gui.ContactList's costructor!!
        self._model = ContactListModel.ContactListModel(session.config, self)
        self._pmodel = ContactListProxy.ContactListProxy(session.config, self)
        gui.ContactList.__init__(self, session)

        self._pmodel.setSourceModel(self._model)
        self.setModel(self._pmodel)
        delegate = ContactListDelegate.ContactListDelegate(session, self)
        delegate.set_nick_formatter(self.format_nick)
        self.setItemDelegate(delegate)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection);
        self.setAnimated(True)
        self.setRootIsDecorated(False)
        self.setHeaderHidden(True)
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.setSortingEnabled(True)
        self.viewport().setStyleSheet('QWidget{                    \
            background-attachment: fixed;           \
            background-origin: content;             \
            background-position: bottom left;       \
            background-repeat: no-repeat;           \
            background-clip: content;}')
        self.setIndentation(0)
        self.doubleClicked.connect(self._on_item_double_clicked)


    # [START] -------------------- GUI.CONTACTLIST_OVERRIDE

    def add_contact(self, contact, group=None):
        '''Add a contact to the view. Resent to model.'''
        self._model.add_contact(contact, group)

    def update_contact(self, contact):
        '''Update a contact in the view. Resent to model'''
        self._model.update_contact(contact)

    def remove_contact(self, contact, group=None):
        '''remove a contact from the specified group, if group is None
        then remove him from all groups'''
        log.debug('remove contact: [%s,%s]' % (contact, group))
        #FIXME: implement contact remove

    def add_group(self, group):
        '''Add a group to the view. Resent to model.'''
        self._model.add_group(group)

    def fill(self, clear=True):
        '''Fill the contact list. Resent to model'''
        gui.ContactList.fill(self, clear)

    def get_contact_selected(self):
        idx_list = self.selectedIndexes()
        if len(idx_list) != 1:
            return None
        index = idx_list[0]
        if not index.parent().isValid():
            log.debug('Returning None because of group.')
            return None
        return self._pmodel.data(index, Role.DataRole).toPyObject()

    def get_group_selected(self):
        idx_list = self.selectedIndexes()
        index = idx_list[0]
        log.debug('*** GET GROUP SELECTED ***')
        log.debug(index)
        log.debug(' --> (%d, %d)[%s]' % (index.row(), index.column(), index.isValid()))
        if len(idx_list) > 1 :
            log.debug('Returning None because of len>1')
            return None
        if index.parent().isValid():
            log.debug('Returning None because of contact.')
            return None
        log.debug('Returning %s' % self._pmodel.data(index, Role.DataRole).toPyObject())
        return self._pmodel.data(index, Role.DataRole).toPyObject()

    def open_conversation(self, *args):
        """
        Opens a new conversation if a contact is selected
        """
        contact = self.get_contact_selected()
        if contact:
            self.new_conversation_requested.emit(str(contact.account))

    def clear(self):
        '''Clears the contact list. Resent to model.'''
        self._model.clear()
        return True

    def refilter(self):
        self._pmodel.set_filter_text(self.filter_text)

    def expand_groups(self):
        ''' expand groups while searching'''
        if self.is_searching:
            self.expandAll()

    def un_expand_groups(self):
        ''' restore groups after a search'''
        # deactivate animations to avoid visual noise
        self.setAnimated(False)
        for index in range(0, self._pmodel.rowCount()):
            selected_index = self._pmodel.index(index, 0)
            if selected_index.parent().isValid():
                continue
            group = self._pmodel.data(selected_index,
                Role.DataRole).toPyObject()
            if group is None:
                group_name = unicode(self._pmodel.data(selected_index,
                Role.DisplayRole).toString())
            else:
                group_name = group.name
            state = self.group_state.get(group_name, False)
            if state:
                self.setExpanded(selected_index, False)
        # reactivate animations
        self.setAnimated(True)

    def select_top_contact(self):
        selection = QtGui.QItemSelectionModel(self._pmodel)
        index = self._pmodel.index(0, 0)
        #check for contact
        if not index.parent().isValid():
            index = index.child(0,0)
        selection = self.selectionModel()
        selection.select(index, QtGui.QItemSelectionModel.Select)

    # [END] -------------------- GUI.CONTACTLIST_OVERRIDE

    def _on_item_double_clicked(self, index):
        '''Slot called when the user double clicks a contact. requests
        a new conversation'''
        if index.parent().isValid():
            contact = self._pmodel.data(index, Role.DataRole).toPyObject()
            self.new_conversation_requested.emit(str(contact.account))
        else:
            group = self._pmodel.data(index, Role.DataRole).toPyObject()
            if not group:
                return
            if self.isExpanded(index):
                self.on_group_expanded(group)
            else:
                self.on_group_collapsed(group)

    def escaper(self, text):
        ''' escape the text, this is a toolkit dependant method '''
        return unicode(text)
