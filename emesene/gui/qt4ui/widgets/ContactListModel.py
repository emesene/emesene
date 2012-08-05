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

'''This module constains the ContactListModel class'''

import logging
import xml

import PyQt4.QtGui as QtGui
import PyQt4.QtCore as QtCore
from PyQt4.QtCore import Qt

from gui.qt4ui import Utils
from gui.qt4ui.Utils import tr

import e3

log = logging.getLogger('qt4ui.widgets.ContactListModel')


class ContactListModel (QtGui.QStandardItemModel):
    '''Item model which represents a contact list'''

    sort_role_dict = {e3.status.ONLINE: u'00',
                       e3.status.BUSY: u'10',
                       e3.status.AWAY: u'20',
                       e3.status.IDLE: u'30',
                       e3.status.OFFLINE: u'40'}

    NO_GRP_UID = 'nogroup'
    ONL_GRP_UID = 'onlinegroup'
    OFF_GRP_UID = 'offlinegroup'

    def __init__(self, config, parent=None):
        '''Constructor'''
        QtGui.QStandardItemModel.__init__(self, parent)
        self.setSortRole(Role.SortRole)

        self._no_grp = self._search_item(self.NO_GRP_UID, self)
        self._onl_grp = self._search_item(self.ONL_GRP_UID, self)
        self._off_grp = self._search_item(self.OFF_GRP_UID, self)

        self._config = config
        self._show_offline = config.b_show_offline
        self._show_empty = config.b_show_empty_groups
        self._show_blocked = config.b_show_blocked
        self._order_by_group = config.b_order_by_group
        self._group_offline = config.b_group_offline

        config.subscribe(self._on_cc_show_offline, 'b_show_offline')
        config.subscribe(self._on_cc_show_empty, 'b_show_empty_groups')
        config.subscribe(self._on_cc_show_blocked, 'b_show_blocked')
        config.subscribe(self._on_cc_order_by_group, 'b_order_by_group')
        config.subscribe(self._on_cc_group_offline, 'b_group_offline')

    def add_contact(self, contact, group=None):
        '''Add a contact'''
        # decide in which group we have to add the contact:
        if self._config.b_order_by_group:
            if not group:
                group_uid = self.NO_GRP_UID
            else:
                group_uid = group.identifier
        else:
            if contact.status == e3.status.OFFLINE:
                group_uid = self.OFF_GRP_UID
            else:
                group_uid = self.ONL_GRP_UID

        # if the target group is not the offline group add the contact:
        # (we skip the offline group because it is a target group each
        # time a contact is offline, for convenience.)
        if not self._config.b_order_by_group or group_uid != self.OFF_GRP_UID:
            group_item = self._search_item(group_uid, self)
            new_contact_item = QtGui.QStandardItem(contact.display_name)
            new_contact_item.setData(contact.identifier, Role.UidRole)
            self._set_contact_info(new_contact_item, contact)
            group_item.appendRow(new_contact_item)
            # increment the total count:
            tot_count = group_item.data(Role.TotalCountRole).toPyObject()
            group_item.setData(tot_count + 1, Role.TotalCountRole)
            if contact.status != e3.status.OFFLINE:
                # increment the online count:
                onl_count = group_item.data(Role.OnlCountRole).toPyObject()
                group_item.setData(tot_count + 1, Role.OnlCountRole)

        if self._config.b_order_by_group and \
                                        contact.status == e3.status.OFFLINE:
            group_item = self._search_item(self.OFF_GRP_UID, self)
            new_contact_item = QtGui.QStandardItem(contact.display_name)
            new_contact_item.setData(contact.identifier + 'FLN', Role.UidRole)
            self._set_contact_info(new_contact_item, contact)
            group_item.appendRow(new_contact_item)
            # increment the total count:
            tot_count = group_item.data(Role.TotalCountRole).toPyObject()
            group_item.setData(tot_count + 1, Role.TotalCountRole)
            # increment the online count:
            onl_count = group_item.data(Role.OnlCountRole).toPyObject()
            group_item.setData(onl_count + 1, Role.OnlCountRole)
        #self.refilter()

    def update_contact(self, contact):
        '''Update a contact'''
        # TODO: Keep a {contact uid:group item} dict... maybe..
        # btw this method is horrible...
        if self._config.b_order_by_group:
            for index in range(self.rowCount()):
                group_item = self.item(index, 0)
                if group_item == self._off_grp:
                    continue
                contact_item = self._search_item(contact.identifier,
                                                 group_item)
                if contact_item:
                    break

            if not contact_item:
                log.debug('***** NOT FOUND: %s' % (contact))
                return

            old_status = contact_item.data(Role.StatusRole)
            new_status = contact.status
            off_status = e3.status.OFFLINE

            self._set_contact_info(contact_item, contact)

            if old_status == off_status:
                contact_item = self._search_item(contact.identifier + 'FLN',
                                                 self._off_grp)
                self._set_contact_info(contact_item, contact)

            if old_status == off_status and new_status != off_status:
                # If this block is executed then for sure the previous one has
                # been executed too. So contact_item is the offline one
                self._off_grp.removeRow(contact_item.index().row())
                # increment the onlie count:
                onl_count = group_item.data(Role.OnlCountRole).toPyObject()
                group_item.setData(onl_count+1, Role.OnlCountRole)

            if old_status != off_status and new_status == off_status:
                contact_item = contact_item.clone()
                contact_item.setData(str(
                        contact_item.data(Role.UidRole).toPyObject()) + 'FLN',
                        Role.UidRole)
                self._off_grp.appendRow(contact_item)
                # decrement the online count:
                onl_count = group_item.data(Role.OnlCountRole).toPyObject()
                group_item.setData(onl_count-1, Role.OnlCountRole)
                # increment the online count:
                onl_count = self._off_grp.data(Role.OnlCountRole).toPyObject()
                self._off_grp.setData(onl_count+1, Role.OnlCountRole)
        else:
            contact_item = self._search_item(contact.identifier, self._onl_grp)

            if contact_item:
                new_status = contact.status
                self._set_contact_info(contact_item, contact)
                if new_status == e3.status.OFFLINE:
                    self._onl_grp.takeRow(contact_item.index().row())
                    self._off_grp.appendRow(contact_item)
                    # increment the online count:
                    onl_count = self._off_grp.data(Role.OnlCountRole).toPyObject()
                    self._off_grp.setData(onl_count+1, Role.OnlCountRole)
                    # decrement the online count:
                    onl_count = self._onl_grp.data(Role.OnlCountRole).toPyObject()
                    self._onl_grp.setData(onl_count-1, Role.OnlCountRole)
            else:
                contact_item = self._search_item(contact.identifier,
                                                 self._off_grp)
                if not contact_item:
                    log.debug('***** NOT FOUND: %s' % (contact))
                    return
                new_status = contact.status
                self._set_contact_info(contact_item, contact)
                if new_status != e3.status.OFFLINE:
                    self._off_grp.takeRow(contact_item.index().row())
                    self._onl_grp.appendRow(contact_item)
                    # decrement the online count:
                    onl_count = self._off_grp.data(Role.OnlCountRole).toPyObject()
                    self._off_grp.setData(onl_count - 1, Role.OnlCountRole)
                    # increment the online count:
                    onl_count = self._onl_grp.data(Role.OnlCountRole).toPyObject()
                    self._onl_grp.setData(onl_count + 1, Role.OnlCountRole)
        #self.refilter()

    def _set_contact_info(self, contact_item, contact):
        '''Fills the contact Item with data'''
        # TODO: handle moving contact between groups
        # in particular: online/offiline
        display_name = Utils.escape(unicode(contact.display_name))
        message = Utils.escape(unicode(contact.message))
        sort_role = self.sort_role_dict[contact.status] + display_name

        contact_item.setData(display_name, Role.DisplayRole)
        contact_item.setData(message, Role.MessageRole)
        contact_item.setData(contact.picture, Role.DecorationRole)
        contact_item.setData(contact.media, Role.MediaRole)
        contact_item.setData(contact.status, Role.StatusRole)
        contact_item.setData(contact.blocked, Role.BlockedRole)
        contact_item.setData(contact.account, Role.ToolTipRole)
        contact_item.setData(sort_role, Role.SortRole)
        contact_item.setData(contact, Role.DataRole)
        #self.sort(0)

    def _set_filter_role(self, index):
        '''Sets the filter role data filed on the given element'''
        filter_role = True
        if not index.parent().isValid():
            # 1) Special Groups:
            uid = self.data(index, Role.UidRole).toPyObject()
            if  uid == self.ONL_GRP_UID and self._order_by_group:
                filter_role = False
            if  uid == self.OFF_GRP_UID and not self._group_offline:
                filter_role = False
            # 2) Check for empty groups
            if not self._show_empty and self._is_group_empty(index):
                filter_role = False
        else:
            blocked = self.data(index, Role.BlockedRole).toPyObject()
            status = self.data(index, Role.StatusRole).toPyObject()
            parent_uid = self.data(index.parent(), Role.UidRole).toPyObject()
            # 3) Blocked Contacts:
            if blocked and not self._show_blocked:
                filter_role = False
            # 4) Offline Contacts:
            if status == e3.status.OFFLINE and parent_uid != self.OFF_GRP_UID \
                and not self._show_offline:
                filter_role = False
        self.dataChanged.emit(index, index)
        self.setData(index, filter_role, Role.FilterRole)

    def refilter(self):
        '''Recalculates filtering for each element in the model'''
        for i in range(self.rowCount()):
            group_index = self.index(i, 0)
            for j in range(self.rowCount(group_index)):
                contact_index = self.index(j, 0, group_index)
                self._set_filter_role(contact_index)
            self._set_filter_role(group_index)

    def _is_group_empty(self, index):
        '''Checks if a group has no visible child'''
        if index.parent().isValid():
            raise ValueError('Not a group')
        group_item = self.itemFromIndex(index)
        for i in range(group_item.rowCount()):
            contact_item = group_item.child(i, 0)
            if contact_item.data(Role.FilterRole) == True:
                #found one visible contact
                return True
        return False

    def add_group(self, group):
        '''Add a group.'''
        if not self._config.b_order_by_group:
            return

        new_group_item = QtGui.QStandardItem(
                    Utils.escape(unicode(group.name)))
        new_group_item.setData(group.identifier, Role.UidRole)
        new_group_item.setData(0, Role.TotalCountRole)
        new_group_item.setData(0, Role.OnlCountRole)
        new_group_item.setData(group, Role.DataRole)
        self.appendRow(new_group_item)
        #self.refilter()

    def clear(self):
        '''Clears the model'''
        QtGui.QStandardItemModel.clear(self)
        self._no_grp = self._search_item(self.NO_GRP_UID, self)
        self._onl_grp = self._search_item(self.ONL_GRP_UID, self)
        self._off_grp = self._search_item(self.OFF_GRP_UID, self)

    def _search_item(self, uid, parent):
        # TODO: refactor
        '''Searches na item, given its uid'''
        if parent == self:
            item_locator = parent.item
        else:
            item_locator = parent.child

        num_rows = parent.rowCount()
        for i in range(num_rows):
            found_item = item_locator(i, 0)
            found_uid = found_item.data(Role.UidRole).toString()
            if found_uid == QtCore.QString(str(uid)).trimmed():
                return found_item
        if uid in [self.NO_GRP_UID, self.ONL_GRP_UID, self.OFF_GRP_UID]:
            if uid == self.NO_GRP_UID:
                group = e3.Group(tr("No group"), identifier='0', type_ = e3.Group.NONE)
            elif uid == self.ONL_GRP_UID:
                group = e3.Group(tr("Online"), identifier='0', type_=e3.Group.ONLINE)
            elif uid == self.OFF_GRP_UID:
                group = e3.Group(tr("Offline"), identifier='1', type_=e3.Group.OFFLINE)
            new_group_item = QtGui.QStandardItem(group.name)
            new_group_item.setData(uid, Role.UidRole)
            new_group_item.setData(0, Role.TotalCountRole)
            new_group_item.setData(0, Role.OnlCountRole)
            new_group_item.setData(group, Role.DataRole)
            self.appendRow(new_group_item)
            return new_group_item

    # cc = configchange
    def _on_cc_show_offline(self, value):
        self._show_offline = value
        #self.refilter()

    def _on_cc_show_empty(self, value):
        self._show_empty = value
        #self.refilter()

    def _on_cc_show_blocked(self, value):
        self._show_blocked = value
        #self.refilter()

    def _on_cc_order_by_group(self, value):
        self._order_by_group = value
        #self.refilter()

    def _on_cc_group_offline(self, value):
        self._group_offline = value
        #self.refilter()

    def remove_subscriptions(self):
        self._config.unsubscribe(self._on_cc_show_offline, 'b_show_offline')
        self._config.unsubscribe(self._on_cc_show_empty, 'b_show_empty_groups')
        self._config.unsubscribe(self._on_cc_show_blocked, 'b_show_blocked')
        self._config.unsubscribe(self._on_cc_order_by_group, 'b_order_by_group')
        self._config.unsubscribe(self._on_cc_group_offline, 'b_group_offline')


class Role (object):
    '''A Class representing various custom Qt User Roles'''
    def __init__(self):
        '''Constructor'''
        pass
    DisplayRole = Qt.DisplayRole
    DecorationRole = Qt.DecorationRole
    ToolTipRole = Qt.ToolTipRole
    BlockedRole = Qt.UserRole
    DataRole = Qt.UserRole + 1
    MediaRole = Qt.UserRole + 2
    UidRole = Qt.UserRole + 3
    SortRole = Qt.UserRole + 4
    StatusRole = Qt.UserRole + 5
    MessageRole = Qt.UserRole + 6
    FilterRole = Qt.UserRole + 7
    TotalCountRole = Qt.UserRole + 8
    OnlCountRole = Qt.UserRole + 9
