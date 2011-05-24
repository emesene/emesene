# -*- coding: utf-8 -*-

'''This module contains menu widgets' classes'''

import PyQt4.QtGui      as QtGui

import gui

ICON = QtGui.QIcon.fromTheme

class ContactMenu(QtGui.QMenu):
    '''A class that represents a menu to handle contact related information'''
    NAME = 'Contact Menu'
    DESCRIPTION = 'The menu that displays contact options'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    def __init__(self, handler, parent=None):
        '''
        constructor

        handler -- a e3common.Handler.ContactHandler
        '''
        QtGui.QMenu.__init__(self, 'Contact', parent)
        self._handler = handler

        
        self._action_d = {}
        action_d = self._action_d
        action_d['add']     = QtGui.QAction(ICON('list-add'),       'Add',     self)
        action_d['remove']  = QtGui.QAction(ICON('list-remove'),    'Remove',  self)
        action_d['block']   = QtGui.QAction(ICON('dialog-cancel'),  'Block',   self)
        action_d['unblock'] = QtGui.QAction(ICON('dialog-ok-apply'), 
                                       'Unblock', self)
        action_d['move_to']     = QtGui.QMenu('Move to group',      self)
        action_d['copy_to']     = QtGui.QMenu('Copy to group',      self)
        action_d['remove_from'] = QtGui.QMenu('Remove from group',  self)
        action_d['set_alias']   = QtGui.QAction('Set alias...',       self)
        action_d['view_info']   = QtGui.QAction('View info...',       self)
        
        self.addActions( (action_d['add'],
                          action_d['remove'],
                          action_d['block'],
                          action_d['unblock']) )
        self.addMenu(     action_d['move_to'])
        self.addMenu(     action_d['copy_to'])
        self.addMenu(     action_d['remove_from'])
        self.addActions( (action_d['set_alias'],
                          action_d['view_info']) )
        
        self.setIcon(QtGui.QIcon(gui.theme.user))
        
        self.aboutToShow.connect(
            lambda *args: self._update_groups())
        action_d['add'].triggered.connect(
            lambda *args: self._handler.on_add_contact_selected())
        action_d['remove'].triggered.connect(
            lambda *args: self._handler.on_remove_contact_selected())
        action_d['block'].triggered.connect(
            lambda *args: self._handler.on_block_contact_selected())
        action_d['unblock'].triggered.connect(
            lambda *args: self._handler.on_unblock_contact_selected())
        action_d['set_alias'].triggered.connect(
            lambda *args: self._handler.on_set_alias_contact_selected())
        action_d['view_info'].triggered.connect(
            lambda *args: self._handler.on_view_information_selected())
        
        
        
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
                    action1 = QtGui.QAction(group.name, self)
                    action2 = QtGui.QAction(group.name, self)
                    action1.setData(group)
                    action2.setData(group)
                    move_to.addAction(action1)
                    copy_to.addAction(action2)
                    move_to.triggered.connect(self._on_move_to_group)
                    copy_to.triggered.connect(self._on_copy_to_group)
                else:
                    action = QtGui.QAction(group.name, self)
                    action.triggered.connect(
                        lambda *args: handler.on_remove_from_group_selected(group))
                    remove_from.addAction(action)
                
        # Deactivate the submenus if they're empty:
        move_to.setEnabled(    not move_to.isEmpty())
        copy_to.setEnabled(    not copy_to.isEmpty())
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
            
        
        
