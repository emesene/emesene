# -*- coding: utf-8 -*-

'''This module contains classes needed to the debug window'''

#import os

from PyQt4  import QtGui
#from PyQt4  import QtCore

#import extension
#import gui
#from gui.qt4ui import Dialog
#from gui.qt4ui import widgets

class DebugWindow(QtGui.QWidget):
    '''A Window which shows debug messages'''
    NAME = 'Debug Window'
    DESCRIPTION = 'A window which shows debug messages'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        
        self._widget_d['filter_edit'] = QtGui.QLineEdit()
        self._widget_d['msg_level_combo'] = QtGui.QComboBox()
        self._widget_d['filter_btn'] = QtGui.QPushButton(_('Filter'))
        hlay = QtGui.QHBoxLayout()
        lay.addWidget(self._widget_d['filter_edit'])
        lay.addWidget(self._widget_d['filter_edit'])
        self.setLayout(lay)
        # FIXME: dangerous circular reference!
        self._myself = self
    
    def show(self):
        print 'DEBUG'
        QtGui.QWidget.show(self)
