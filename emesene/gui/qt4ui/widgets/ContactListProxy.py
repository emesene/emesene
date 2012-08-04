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
'''This module constains the ContactListProxy class'''

import logging

import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore
from PyQt4.QtCore import Qt

import e3
from gui.qt4ui.widgets.ContactListModel import ContactListModel
from gui.qt4ui.widgets.ContactListModel import Role

log = logging.getLogger('qt4ui.widgets.ContactListProxy')


class ContactListProxy (QtGui.QSortFilterProxyModel):
    '''This class provides a proxy to access the contact list
    data model. This proxy Exports contact list's information
    according to user settings such as: 'Show offline groups',
    'Show empty groups', etc...'''

    def __init__(self, config, parent=None):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        self._internal_proxy = InternalContactListProxy(config, self)
        QtGui.QSortFilterProxyModel.setSourceModel(self, self._internal_proxy)
        self.setSortRole(Role.SortRole)
        self.setDynamicSortFilter(True)
        self._config = config
        #config = session.config
        self._show_empty = config.b_show_empty_groups
        self._group_offline = config.b_group_offline
        self._show_offline = config.b_show_offline

        config.subscribe(self._on_cc_group_offline, 'b_group_offline')
        config.subscribe(self._on_cc_show_empty_groups, 'b_show_empty_groups')
        config.subscribe(self._on_cc_show_offline, 'b_show_offline')

    def setSourceModel(self, source_model):
        self.sourceModel().setSourceModel(source_model)

    def set_filter_text(self, filter_text):
        if filter_text != '':
            self._show_empty = False
            self._show_offline = False
        else:
            self._show_empty = self._config.b_show_empty_groups
            self._show_offline = self._config.b_show_offline
        self._internal_proxy.set_filter_text(filter_text)
        self._internal_proxy._show_offline = self._show_offline
        self.invalidateFilter()

    def filterAcceptsRow(self, row, parent_idx):
        model = self.sourceModel()
        index = model.index(row, 0, parent_idx)
        # Filtering groups:
        if not index.parent().isValid():
            uid = model.data(index, Role.UidRole).toPyObject()
            if self._config.b_order_by_group and \
                uid == ContactListModel.ONL_GRP_UID:
                    return False
            if not self._group_offline and \
               uid == ContactListModel.OFF_GRP_UID:
                    return False

            if not self._show_empty and \
                model.rowCount(index) == 0:
                    # well here we should effectively /count/ the items...
                    return False
        return True

    def sort(self, column, order):
        QtGui.QSortFilterProxyModel.sort(self, 0, Qt.AscendingOrder)

    # cc = configchange
    def _on_cc_group_offline(self, value):
        self._group_offline = value
        self.invalidateFilter()

    def _on_cc_show_empty_groups(self, value):
        self._show_empty = value
        self.invalidateFilter()

    def _on_cc_show_offline(self, value):
        self._show_offline = value
#        self._config.b_show_empty_groups = not self._config.b_show_empty_groups
        self.invalidateFilter()


class InternalContactListProxy (QtGui.QSortFilterProxyModel):
    '''This class provides a proxy to access the contact list
    data model. This proxy Exports contact list's information
    according to user settings such as: 'Show offline groups',
    'Show empty groups', etc...'''

    def __init__(self, config, parent=None):
        QtGui.QSortFilterProxyModel.__init__(self, parent)

        self.setSortRole(Role.SortRole)
        self.setDynamicSortFilter(True)
        self._filter_text = QtCore.QString('')
        #config = session.config
        self._config = config
        self._show_offline = config.b_show_offline
        self._show_blocked = config.b_show_blocked
        self._group_offline = config.b_group_offline

        config.subscribe(self._on_cc_show_offline, 'b_show_offline')
        config.subscribe(self._on_cc_group_offline, 'b_group_offline')
        config.subscribe(self._on_cc_show_blocked, 'b_show_blocked')

    def set_filter_text(self, filter_text):
        self._filter_text = QtCore.QString(filter_text)
        self.invalidateFilter()

    def filterAcceptsRow(self, row, parent_idx):
        model = self.sourceModel()
        index = model.index(row, 0, parent_idx)

        # Filtering just contacts:
        if index.parent().isValid():
            #FIXME: sometimes we get an 'str' instance
            if isinstance(self._filter_text, basestring):
                self._filter_text = QtCore.QString(self._filter_text)

            if not self._filter_text.isEmpty():
                contact_name = model.data(index, Role.DisplayRole).toString()
                contact_message = model.data(index, Role.MessageRole).toString()
                contact_account = model.data(index, Role.ToolTipRole).toString()
                if (contact_name.indexOf(self._filter_text) != -1 or
                    contact_message.indexOf(self._filter_text) != -1 or
                    contact_account.indexOf(self._filter_text) != -1):
                    return True
                else:
                    return False

            if not self._show_offline and \
               model.data(index, Role.StatusRole) == e3.status.OFFLINE:
                    self.dataChanged.emit(self.mapFromSource(index.parent()),
                        self.mapFromSource(index.parent()))
                    return False

            if not self._show_blocked and \
               model.data(index, Role.BlockedRole).toBool():
                    self.dataChanged.emit(self.mapFromSource(index.parent()),
                        self.mapFromSource(index.parent()))
                    return False

            if self._group_offline and \
                model.data(index, Role.StatusRole) == e3.status.OFFLINE and \
                model.data(index.parent(), Role.UidRole) != ContactListModel.OFF_GRP_UID:
                    self.dataChanged.emit(self.mapFromSource(index.parent()),
                                          self.mapFromSource(index.parent()))
                    return False

        self.dataChanged.emit(self.mapFromSource(index.parent()),
                              self.mapFromSource(index.parent()))
        return True

    def sort(self, column, order):
        pass

    # cc = configchange
    def _on_cc_group_offline(self, value):
        self._group_offline = value
        self.invalidateFilter()

    def _on_cc_show_offline(self, value):
        self._show_offline = value
        self.invalidateFilter()

    def _on_cc_show_blocked(self, value):
        self._show_blocked = value
        self.invalidateFilter()
