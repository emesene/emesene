# -*- coding: utf-8 -*-

'''This module contains menu widgets' classes'''


import PyQt4.QtGui      as QtGui

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
        QtGui.QMenu.__init__(self, 'Status', parent)
        self._on_status_selected = on_status_selected
        self._status_actions = {}

        for stat in e3.status.ORDERED:
            temp_item = QtGui.QAction(
                    QtGui.QIcon(QtGui.QPixmap(gui.theme.status_icons[stat])),
                    e3.status.STATUS[stat],
                    self)
            temp_item.triggered.connect(self._on_activate)
            self._status_actions[stat] = temp_item
            self.addAction(temp_item)

    def _on_activate(self):
        '''method called when a status menu item is called'''

        self._on_status_selected(e3.status.ONLINE)
