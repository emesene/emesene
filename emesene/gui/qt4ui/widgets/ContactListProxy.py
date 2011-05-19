# -*- coding: utf-8 -*-

'''This module constains the ContactListProxy class'''

import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

import e3

from gui.qt4ui  import Utils
from gui.qt4ui.widgets.ContactListModel import ContactListModel
from gui.qt4ui.widgets.ContactListModel import Role

#class ContactListProxy435 (QtGui.QSortFilterProxyModel):
#    def __init__(self, config, parent=None):
#        QtGui.QSortFilterProxyModel.__init__(self, parent)
#        
#        self.setSortRole(Role.SortRole)
#        self.setDynamicSortFilter(True)
#        
#    def filterAcceptsRow(self, row, parent_idx):
#        model = self.sourceModel()
#        index = model.index(row, 0, parent_idx)
#        print 'FR: %s[%s]' % (self.data(index, Role.FilterRole).toPyObject(), 
#                              index.isValid())
#        return self.data(index, Role.FilterRole).toPyObject()
            
    

class ContactListProxy (QtGui.QSortFilterProxyModel):
    '''This class provides a proxy to access the contact list
    data model. This proxy Exports contact list's information
    according to user settings such as: 'Show offline groups', 
    'Show empty groups', etc...'''
    
    def __init__(self, config, parent=None):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        QtGui.QSortFilterProxyModel.setSourceModel(self, 
                                            InternalContactListProxy(config, 
                                                                     self  ))
        
        self.setSortRole(Role.SortRole)
        self.setDynamicSortFilter(True)
        
        self._config = config
        #config = session.config
        self._show_empty     = config.b_show_empty_groups
        self._group_offline  = config.b_group_offline
        
        config.subscribe(self._on_cc_group_offline,     'b_group_offline')
        config.subscribe(self._on_cc_show_empty_groups, 'b_show_empty_groups')
        config.subscribe(self._on_cc_show_empty_groups, 'b_show_offline')
        
    def setSourceModel(self, source_model):
        self.sourceModel().setSourceModel(source_model)
        
    def filterAcceptsRow (self, row, parent_idx):
        model = self.sourceModel()
        index = model.index(row, 0, parent_idx)
        # Filtering groups:
        if not index.parent().isValid():
            uid = model.data(index, Role.UidRole).toPyObject()
            if self._config.b_order_by_group and \
                uid == ContactListModel.ONL_GRP_UID :
                    print '*** Group %s filtered because of _order_by_group=%s' % (
                            model.data(index, Role.DisplayRole).toString(), self._config.b_order_by_group)
                    return False
            if not self._config.b_group_offline and \
               uid == ContactListModel.OFF_GRP_UID:
                   print '*** Group %s filtered because of _group_offline=%s' % (
                        model.data(index, Role.DisplayRole).toString(), self._group_offline)
                   return False
                   
            if not self._config.b_show_empty_groups and \
                model.rowCount(index) == 0:
                    # well here we should effectively /count/ the items...
                    print '*** Group %s filtered because of _show_empty = %s [%d]' % (
                        model.data(index, Role.DisplayRole).toString(), self._config.b_show_empty_groups, model.rowCount(index))
                    return False
                    
                   
        print '*** Showing group: %s [%d]' % (model.data(index, Role.DisplayRole).toString(), model.rowCount(index))
        return True
            
        
    def sort(self, column, order):
        print 'About to Sort'
        QtGui.QSortFilterProxyModel.sort(self, 0, Qt.AscendingOrder)  
       
    # cc = configchange       
    def _on_cc_group_offline(self, value):
        self._group_offline = value
        self.invalidateFilter()
           
    def _on_cc_show_empty_groups(self, value):
        self._show_empty = value
        print '*'
        self.invalidateFilter()
    
    def _on_cc_show_offline(self, value):
        print '----------> SHOW OFFLINE: %s' % value
        self._show_offline = value
        self._config.b_show_empty_groups = not self._config.b_show_empty_groups
        self._config.b_show_empty_groups = not self._config.b_show_empty_groups
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
        
        #config = session.config
        self._config = config
        self._show_offline   = config.b_show_offline
        self._show_blocked   = config.b_show_blocked
        self._group_offline  = config.b_group_offline
        
        config.subscribe(self._on_cc_show_offline,  'b_show_offline')
        config.subscribe(self._on_cc_group_offline, 'b_group_offline')
        
        
    def filterAcceptsRow (self, row, parent_idx):
        model = self.sourceModel()
        index = model.index(row, 0, parent_idx)
        
        # Filtering just contacts:
        if index.parent().isValid():
            
            if not self._config.b_show_offline and \
               model.data(index, Role.StatusRole) == e3.status.OFFLINE:
                   print '****** Contact %s filtered because of _show_offline=%s' % (
                        model.data(index, Role.DisplayRole).toString(), self._show_offline)
                   self.dataChanged.emit(self.mapFromSource(index.parent()),
                                         self.mapFromSource(index.parent()))
                   return False
                   
            if self._config.b_group_offline and \
                model.data(index, Role.StatusRole) == e3.status.OFFLINE and \
                model.data(index.parent(), Role.UidRole) != ContactListModel.OFF_GRP_UID:
                    print '****** Contact %s filtered because of _group_offline=%s' % (
                        model.data(index, Role.DisplayRole).toString(), self._group_offline)
                    self.dataChanged.emit(self.mapFromSource(index.parent()),
                                          self.mapFromSource(index.parent()))
                    return False
                   
        print '****** Showing contact: %s' % model.data(index, Role.DisplayRole).toString()          
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
        print '----------> SHOW OFFLINE: %s' % value
        self._show_offline = value
        self.invalidateFilter()
       
       
