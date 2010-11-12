# -*- coding: utf-8 -*-

'''This module constains the ContactListModel class'''

import xml

import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

from gui.qt4ui  import Utils

import e3

class ContactListModel (QtGui.QStandardItemModel):
    '''Item model which represents a contact list'''
    # TODO: generate this on the fly in the constructor.
    sort_role_dict = { e3.status.ONLINE  : u'00',
                       e3.status.BUSY    : u'10',
                       e3.status.AWAY    : u'20',
                       e3.status.IDLE    : u'30',
                       e3.status.OFFLINE : u'40' }
                    
    NO_GRP_UID  = 'nogroup'
    ONL_GRP_UID = 'onlinegroup'
    OFF_GRP_UID = 'offlinegroup'
    
    def __init__(self, config, parent=None):
        '''Constructor'''
        QtGui.QStandardItemModel.__init__(self,  parent)
        self.setSortRole(Role.SortRole)
        
        self._no_grp  = self._search_item(self.NO_GRP_UID, self)
        self._onl_grp = self._search_item(self.ONL_GRP_UID, self)
        self._off_grp = self._search_item(self.OFF_GRP_UID, self)
        
        self._show_offline   = config.b_show_offline
        self._show_empty     = config.b_show_empty_groups
        self._show_blocked   = config.b_show_blocked
        self._order_by_group = config.b_order_by_group
        self._group_offline  = config.b_group_offline
        
        config.subscribe(self._on_cc_show_offline, 'b_show_offline')
        config.subscribe(self._on_cc_show_empty, 'b_show_empty_groups')
        config.subscribe(self._on_cc_show_blocked, 'b_show_blocked')
        config.subscribe(self._on_cc_order_by_group, 'b_order_by_group')
        config.subscribe(self._on_cc_group_offline, 'b_group_offline')
        
        
    def add_contact(self, contact, group=None):
        '''Add a contact'''
        # TODO: check adding an existing contact
        print 'add ',
        print contact.display_name,
        if group:
            gname = group.name
        else:
            gname = 'NONE'
        print ' to group: %s' % gname
        
        # decide in which group we have to add the contact:
        if self._order_by_group:
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
        if not self._order_by_group or group_uid != self.OFF_GRP_UID:
            group_item = self._search_item(group_uid, self)
            new_contact_item = QtGui.QStandardItem(contact.display_name)
            new_contact_item.setData(contact.identifier, Role.UidRole)
            self._set_contact_info(new_contact_item, contact)
            group_item.appendRow(new_contact_item)
        
        if self._order_by_group and contact.status == e3.status.OFFLINE:
            group_item = self._search_item(self.OFF_GRP_UID, self)
            new_contact_item = QtGui.QStandardItem(contact.display_name)
            new_contact_item.setData(contact.identifier+'FLN', Role.UidRole)
            self._set_contact_info(new_contact_item, contact)
            group_item.appendRow(new_contact_item)
        self.refilter()
            
    
    def update_contact(self, contact):
        '''Update a contact'''
        # TODO: Keep a {contact uid:group item} dict... maybe..
        # btw this method is horrible...
        print 'UPDATING ',
        print contact.display_name
        print contact.identifier
        if self._order_by_group:
            for index in range(self.rowCount()):
                group_item = self.item(index, 0)
                if group_item == self._off_grp:
                    continue
                contact_item = self._search_item(contact.identifier, 
                                                 group_item)
                if contact_item:
                    break
                    
            if not contact_item:
                print '***** NOT FOUND: %s' % (contact)
                return
                    
            old_status = contact_item.data(Role.StatusRole)
            new_status = contact.status
            
            self._set_contact_info(contact_item, contact)
            
            if old_status == e3.status.OFFLINE:
                contact_item = self._search_item(contact.identifier+'FLN', self._off_grp)
                self._set_contact_info(contact_item, contact)
            
            if old_status == e3.status.OFFLINE and new_status != e3.status.OFFLINE:
                # If this block is executed then for sure the previous one has
                # been executed too. So contact_item is the offline one
                self._off_grp.removeRow(contact_item.index().row())
                   
            if old_status != e3.status.OFFLINE and new_status == e3.status.OFFLINE:
                contact_item = contact_item.clone()
                contact_item.setData(str(contact_item.data(Role.UidRole).toPyObject())+'FLN', Role.UidRole)
                self._off_grp.appendRow(contact_item)
                
                
                
        else:
            contact_item = self._search_item(contact.identifier, self._onl_grp)
                    
            if contact_item:
                new_status = contact.status
            
                self._set_contact_info(contact_item, contact)
                
                if new_status == e3.status.OFFLINE:
                    self._onl_grp.takeRow(contact_item.index().row())
                    self._off_grp.appendRow(contact_item)
            
            else:
                contact_item = self._search_item(contact.identifier, self._off_grp)
                
                if not contact_item:
                    print '***** NOT FOUND: %s' % (contact)
                    return
                
                new_status = contact.status
                
                self._set_contact_info(contact_item, contact)
                
                if new_status != e3.status.OFFLINE:
                    self._off_grp.takeRow(contact_item.index().row())
                    self._onl_grp.appendRow(contact_item)
        self.refilter()
                
                
            
#        if old_status == e3.status.OFFLINE and new_status != e3.status.OFFLINE:
#            group_item.removeRow(contact_item.index().row())
#               
#        if old_status != e3.status.OFFLINE and new_status == e3.status.OFFLINE:
#            group_item = self._search_item(self._offline_group_uid, self)
#            contact_item = contact_item.clone()
#            contact_item.setData(contact_item.data(Role.UidRole)+'FLN')
#            group_item.appendRow(contact_item)
#            
#            
#        
#            
#        
#        if not contact_item:
#            print '***** NOT FOUND: %s' % (contact)
#            return
#        
#        old_status = contact_item.data(Role.StatusRole)
#        new_status = contact.status
#        
#        self._set_contact_info(contact_item, contact)
#    
#        if old_status == e3.status.OFFLINE and new_status != e3.status.OFFLINE:
#            group_item = self._search_item(self._offline_group_uid, self)
#            group_item.takeRow(contact_item.index().row())
#            if not self._order_by_group:
#                group_item = self._search_item(self._online_group_uid, self)
#                group_item.appendRow(contact_item)
#               
#        if old_status != e3.status.OFFLINE and new_status == e3.status.OFFLINE:
#            if not self._order_by_group:
#                group_item = self._search_item(self._online_group_uid, self)
#                group_item.takeRow(contact_item.index().row())
#            group_item = self._search_item(self._offline_group_uid, self)
#            group_item.appendRow(contact_item)
        
    
    def _set_contact_info(self, contact_item, contact):
        '''Fills the contact Item with data'''
        # TODO: handle moving contact between groups 
        # in particular: online/offiline
        display_name = Utils.escape(unicode(contact.display_name))
        message      = Utils.escape(unicode(contact.message))
        sort_role    = self.sort_role_dict[contact.status] + display_name
        
        contact_item.setData(display_name,      Role.DisplayRole)
        contact_item.setData(message,           Role.MessageRole)
        contact_item.setData(contact.picture,   Role.DecorationRole)
        contact_item.setData(contact.media,     Role.MediaRole)
        contact_item.setData(contact.status,    Role.StatusRole)
        contact_item.setData(contact.blocked,   Role.BlockedRole)
        contact_item.setData(contact.account,   Role.ToolTipRole)
        contact_item.setData(sort_role,         Role.SortRole)
        contact_item.setData(contact,           Role.DataRole)
        #self.sort(0)
        
    def _set_filter_role(self, index):
        filter_role = True
        if not index.parent().isValid():
            # 1) Special Groups:
            uid = self.data(index, Role.UidRole).toPyObject() 
            if  uid == self.ONL_GRP_UID and self._order_by_group:
                filter_role = False
            if  uid == self.OFF_GRP_UID and not self._group_offline:
                filter_role = False
            # 2) Check for empty groups
            if self._is_group_empty(index) and not self._show_empty:
                filter_role = False
        else:
            blocked = self.data(index, Role.BlockedRole).toPyObject()
            status  = self.data(index, Role.StatusRole ).toPyObject()
            parent_uid = self.data(index.parent(), Role.UidRole).toPyObject()
            # 3) Blocked Contacts:
            if blocked and not self._show_blocked:
                filter_role = False
            # 4) Offline Contacts:
            if status == e3.status.OFFLINE and parent_uid != self.OFF_GRP_UID \
                and not self._show_offline:
                filter_role = False
        print '> Setting FR for %s to %s' % (self.data(index, Role.DisplayRole).toString(), filter_role)
        self.dataChanged.emit(index, index)
        self.setData(index, filter_role, Role.FilterRole)
        
    def refilter(self):
        for i in range(self.rowCount()):
            group_index = self.index(i, 0)
            for j in range(self.rowCount(group_index)):
                contact_index = self.index(j, 0, group_index)
                self._set_filter_role(contact_index)
            self._set_filter_role(group_index)
            
    def _is_group_empty(self, index):
        if index.parent().isValid():
            raise ValueError('Not a group')
        visible_contacts = 0
        group_item = self.itemFromIndex(index)
        for i in range (group_item.rowCount()):
            contact_item = group_item.child(i, 0)
            if contact_item.data(Role.FilterRole) == True:
                visible_contacts += 1
        return visible_contacts > 0
        
    def add_group(self, group):
        '''Add a group.'''
        if not self._order_by_group:
            return
        new_group_item = QtGui.QStandardItem( QtCore.QString( 
                    xml.sax.saxutils.escape(group.name)))
        new_group_item.setData(group.identifier, Role.UidRole)
        new_group_item.setData(group, Role.DataRole)
        self.appendRow(new_group_item)
        self.refilter()

    
    def clear(self):
        QtGui.QStandardItemModel.clear(self)
        self._no_grp  = self._search_item(self.NO_GRP_UID, self)
        self._onl_grp = self._search_item(self.ONL_GRP_UID, self)
        self._off_grp  = self._search_item(self.OFF_GRP_UID, self)
        
    def _search_item(self,  uid,  parent):
        # TODO: refactor
        '''Searches na item, given its uid'''
        if parent == self:
            item_locator = parent.item
        else:
            item_locator = parent.child
            
        num_rows = parent.rowCount()
        for i in range(num_rows):
            found_item = item_locator(i,  0)
            found_uid = found_item.data(Role.UidRole).toString()
            if found_uid == QtCore.QString(str(uid)).trimmed():
                return found_item
        if uid in [self.NO_GRP_UID, 
                   self.ONL_GRP_UID, 
                   self.OFF_GRP_UID]:
            group_name = {self.NO_GRP_UID  : u'No Group',
                          self.OFF_GRP_UID : u'Offline' ,
                          self.ONL_GRP_UID : u'Online'  }
            new_group_item = QtGui.QStandardItem(group_name[uid])
            new_group_item.setData(uid, Role.UidRole)
            self.appendRow(new_group_item)
            return new_group_item
            
            
    # cc = configchange
    def _on_cc_show_offline(self, value):
        self._show_offline = value
        self.refilter()
        
    def _on_cc_show_empty(self, value):
        self._show_empty = value
        self.refilter()
        
    def _on_cc_show_blocked(self, value):
        self._show_offline = value
        self.refilter()
        
    def _on_cc_order_by_group(self, value):
        self._order_by_group = value
        self.refilter()

    def _on_cc_group_offline(self, value):
        self._group_offline = value
        self.refilter()
    
    
    

        



class Role:
    '''A Class representing various custom Qt User Roles'''
    def __init__(self):
        '''Constructor'''
        pass
    DisplayRole     = Qt.DisplayRole
    DecorationRole  = Qt.DecorationRole
    ToolTipRole     = Qt.ToolTipRole
    BlockedRole     = Qt.UserRole
    DataRole        = Qt.UserRole + 17
    MediaRole       = Qt.UserRole + 2
    UidRole         = Qt.UserRole + 3
    SortRole        = Qt.UserRole + 4
    StatusRole      = Qt.UserRole + 5
    MessageRole     = Qt.UserRole + 6
    FilterRole      = Qt.UserRole + 7
