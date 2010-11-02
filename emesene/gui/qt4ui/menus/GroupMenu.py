# -*- coding: utf-8 -*-

'''This module contains menu widgets' classes'''

import PyQt4.QtGui      as QtGui

ICON = QtGui.QIcon.fromTheme

class GroupMenu(QtGui.QMenu):
    '''A class that represents a menu to handle contact related information'''
    NAME = 'Group Menu'
    DESCRIPTION = 'The menu that displays all the group options'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    def __init__(self, handler, parent=None):
        """
        constructor

        handler -- a e3common.Handler.GroupHandler
        """
        QtGui.QMenu.__init__(self, 'Group', parent)
        self._handler = handler

        self.add = QtGui.QAction(ICON('list-add'), 'Add', self)
        self.remove = QtGui.QAction(ICON('list-remove'), 'Remove', self)
        self.rename = QtGui.QAction('Rename', self)
        
        self.addAction(self.add)
        self.addAction(self.remove)
        self.addAction(self.rename)

        
        self.add.triggered.connect(
            lambda *args: self._handler.on_add_group_selected())
        self.remove.triggered.connect(
            lambda *args: self._handler.on_remove_group_selected())
        self.rename.triggered.connect(
            lambda *args: self._handler.on_rename_group_selected())


        
