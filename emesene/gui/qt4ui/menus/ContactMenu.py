# -*- coding: utf-8 -*-

'''This module contains menu widgets' classes'''


import PyQt4.QtGui      as QtGui


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

        self.add =       QtGui.QAction('Add', self)
        self.remove =    QtGui.QAction('Remove', self)
        self.block =     QtGui.QAction('Block', self)
        self.unblock =   QtGui.QAction('Unblock', self)
        self.set_alias = QtGui.QAction('Set alias...', self)
        self.view_info = QtGui.QAction('View info...', self)
        
        self.addAction(self.add)
        self.addAction(self.remove)
        self.addAction(self.block)
        self.addAction(self.unblock)
        self.addAction(self.set_alias)
        self.addAction(self.view_info)
        
        self.add.triggered.connect(
            lambda *args: self._handler.on_add_contact_selected())
        self.remove.triggered.connect(
            lambda *args: self._handler.on_remove_contact_selected())
        self.block.triggered.connect(
            lambda *args: self._handler.on_block_contact_selected())
        self.unblock.triggered.connect(
            lambda *args: self._handler.on_unblock_contact_selected())
        self.set_alias.triggered.connect(
            lambda *args: self._handler.on_set_alias_contact_selected())
        self.view_info.triggered.connect(
            lambda *args: self._handler.on_view_information_selected())

       

