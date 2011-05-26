# -*- coding: utf-8 -*-

'''This module contains menu widgets' classes'''


import PyQt4.QtGui      as QtGui

from gui.qt4ui.Utils import tr

import e3
import gui

class StatusMenu (QtGui.QMenu):
    '''A widget that contains the statuses and 
    allows to change the current status'''
    NAME = 'Status Menu'
    DESCRIPTION = 'A menu to select the status'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    def __init__(self, on_status_selected, parent=None):
        '''
        constructor

        on_status_selected -- a callback that receives the status when changed
        '''
        QtGui.QMenu.__init__(self, tr('Status'), parent)
        self._on_status_selected = on_status_selected

        for status in e3.status.ORDERED:
            action = QtGui.QAction(
                    QtGui.QIcon(QtGui.QPixmap(gui.theme.status_icons[status])),
                    unicode(e3.status.STATUS[status]).capitalize(),
                    self)
            action.setData(status)
            self.triggered.connect(self._on_activate)
            self.addAction(action)

    def _on_activate(self, action):
        '''method called when a status menu item is called'''
        status = action.data().toPyObject()
        self._on_status_selected(status)
