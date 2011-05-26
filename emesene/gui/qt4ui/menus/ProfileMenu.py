# -*- coding: utf-8 -*-

'''This module contains menu widgets' classes'''


import PyQt4.QtGui      as QtGui

from gui.qt4ui.Utils import tr


ICON = QtGui.QIcon.fromTheme

class ProfileMenu(QtGui.QMenu):
    '''A class that represents a menu to handle contact related information'''
    NAME = 'Account menu'
    DESCRIPTION = 'The menu to handle account options'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    def __init__(self, handler, parent=None):
        '''
        constructor

        handler -- a e3common.Handler.AccountHandler
        '''
        QtGui.QMenu.__init__(self, tr('Profile'), parent)
        self._handler = handler

        self.change_profile = QtGui.QAction(tr('Change profile'), self)
        self.addAction(self.change_profile)
        
        self.setIcon(ICON('document-properties'))
        
        self.change_profile.triggered.connect(
            lambda *args: self._handler.change_profile())



