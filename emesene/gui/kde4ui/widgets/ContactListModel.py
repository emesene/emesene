# -*- coding: utf-8 -*-

'''This module constains the ContactListModel class'''

#from amsn2.ui.front_ends.kde4.adaptationLayer import KFEThemeManager, KFELog

import PyKDE4.kdeui     as KdeGui
from PyKDE4.kdecore import i18n
import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

# imports for the Test class:

#from contactListDelegate    import  ContactStyledDelegate

import gui

import xml
import sys


class ContactListModel (QtGui.QStandardItemModel):
    '''Item model which represents a contact list'''
    sortRoleDict = {'online'  : "00",
                    'brb'     : "10",
                    'idle'    : "20",
                    'away'    : "30",
                    'phone'   : "40",
                    'lunch'   : "50",
                    'busy'    : "60",
                    'offline' : "99"}
                    
    def __init__(self, parent=None):
        '''Constructor'''
        QtGui.QStandardItemModel.__init__(self,  parent)
        self.setSortRole(Role.SortRole)
        self._no_group_uid = 'nogroup'
        
    
    def add_contact(self, contact, group=None):
        '''Add a contact'''
        if not group:
            group_uid = self._no_group_uid
        else:
            group_uid = group.identifier
        group_item = self._search_item_by_uid(group_uid, self)
        new_contact_item = QtGui.QStandardItem(contact.display_name)
        new_contact_item.setData(contact.identifier, Role.UidRole)
        self._set_contact_info(new_contact_item, contact)
        group_item.appendRow(new_contact_item)
        
    
    def update_contact(self, contact):
        '''Update a contact'''
        # TODO: Keep a {contact uid:group item} dict
        for index in range(self.rowCount()):
            contact_item = self._search_item_by_uid(contact.identifier,  
                                                        self.item(index, 0))
            if contact_item:
                break
        
        if not contact_item:
            print '***** NOT FOUND: %s' % (contact)
            return
        
        self._set_contact_info(contact_item, contact)
        
    
    def _set_contact_info(self, contact_item, contact):
        '''Fills the contact Item with data'''
        contact_item.setData(
            xml.sax.saxutils.escape(contact.display_name) + '<br><i>' + 
            xml.sax.saxutils.escape(contact.message) +'</i>',
            Role.DisplayRole)
        contact_item.setData(contact.picture, Role.DecorationRole)
        contact_item.setData(contact.media, Role.MediaRole)
        contact_item.setData(contact.status, Role.StatusRole)
        contact_item.setData(contact.blocked, Role.BlockedRole)
        contact_item.setData(contact.account, Role.ToolTipRole)
        contact_item.setData(contact, Role.DataRole)
        
        
    def add_group(self, group):
        '''Add a group.'''
        new_group_item = QtGui.QStandardItem( QtCore.QString( 
                    xml.sax.saxutils.escape(group.name)))
        new_group_item.setData(group.identifier, Role.UidRole)
        self.appendRow(new_group_item)
        
        
#    def onContactListUpdated(self, clView):
#        KFELog().l("ContactListModel.onContactListUpdated()", False,  1)
#        for groupUid in clView.group_ids:
#            newGroupItem = QStandardItem(QString(groupUid))
#            newGroupItem.setData(groupUid,  KFERole.UidRole)
#            newGroupItem.setData(QString(groupUid), KFERole.SortRole)
#            self.appendRow(newGroupItem)
#            
#    def onGroupUpdated(self, gView):
#        KFELog().l("ContactListModel.onGroupUpdated()",  False,  1)
#        groupItem = self._search_item_by_uid(gView.uid,  self)
#        groupItem.setData(gView.name.parse_default_smileys().to_HTML_string(),
#                           KFERole.DisplayRole)
#        groupItem.setData(gView.name.to_HTML_string(), KFERole.SortRole)
#        # TODO: set the Icon. 
#        #groupItem.setData()
#        for contactUid in gView.contact_ids:
#            contactItem = self._search_item_by_uid(contactUid,  groupItem)
#            if contactItem == None:
#                newContactItem = QStandardItem(QString(contactUid))
#                newContactItem.setData(contactUid,  KFERole.UidRole)
#                groupItem.appendRow(newContactItem)
#            
#    def onContactUpdated(self, cView):
#        #KFELog().l("ContactListModel.onContactUpdated()", False, 1)
#        #searching the contact in the groups --> we will have to 
#        #mantain a dict ['uid':idx]...
#        for idx in range(self.rowCount()):
#            foundContactItem = self._search_item_by_uid(cView.uid,  
#                                                         self.item(idx, 0))
#            if foundContactItem:
#                break
#        if not foundContactItem:
#            #temp code
#            foundContactItem = QStandardItem(QString())
#            self._search_item_by_uid(
#                       self.__debugGroupUid, self).appendRow(foundContactItem)
#        # setting DisplayRole
#        foundContactItem.setData(
#    cView.name.parse_default_smileys().to_HTML_string(), KFERole.DisplayRole)
#        # setting.... What?!
#        #foundContactItem.setData(cView) ##????
#        # setting DecorationRole
#        _,displayPicPath = cView.dp.imgs[0]
#        if displayPicPath == "dp_nopic":
#            displayPicPath = KFEThemeManager().pathOf("dp_nopic")
#        foundContactItem.setData(QPixmap(displayPicPath).scaled(50,50),  
#                                  KFERole.DecorationRole)
#        # setting SortRole
#        sortString = self.sortRoleDict[cView.status.to_HTML_string()] + \
#                                            cView.name.to_HTML_string()
#        foundContactItem.setData(sortString, KFERole.SortRole)
#        # setting StatusRole
#        foundContactItem.setData(cView.status.to_HTML_string(),  
#                                KFERole.StatusRole)
#        
#        self.sort(0)
        
        
    def _search_item_by_uid(self,  uid,  parent):
        '''Searches na item, given its uid'''
        if parent == self:
            item_locator = parent.item
        else:
            item_locator = parent.child
            
        num_rows = parent.rowCount()
        for i in range(num_rows):
            found_item = item_locator(i,  0)
            found_uid = found_item.data(Role.UidRole).toString()
            #str(uid) is necessary because gid "0" is passed as a int.... -_-;
            if found_uid == QtCore.QString(str(uid)).trimmed():
                return found_item
        if uid == self._no_group_uid:
            new_group_item = QtGui.QStandardItem(QtCore.QString("No Group"))
            new_group_item.setData(self._no_group_uid, Role.UidRole)
            self.appendRow(new_group_item)
            return new_group_item


class Role:
    '''A Class representing various custom Qt User Roles'''
    def __init__(self):
        '''Constructor'''
        pass
    DisplayRole     = Qt.DisplayRole
    DecorationRole  = Qt.DecorationRole
    ToolTipRole     = Qt.ToolTipRole
    BlockedRole     = Qt.UserRole
    DataRole        = Qt.UserRole + 1
    MediaRole       = Qt.UserRole + 2
    UidRole         = Qt.UserRole + 3
    SortRole        = Qt.UserRole + 4
    StatusRole      = Qt.UserRole + 5 
