# -*- coding: utf-8 -*-

'''This module contains classes needed to the debug window'''

import logging
import time

from PyQt4  import QtGui
#from PyQt4  import QtCore

import debugger
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
        
        self._widget_d = {}
        self._setup_ui()
        
        logging.getLogger().addHandler(self._widget_d['text_view'])
        
        
        # FIXME: dangerous circular reference!
        self._myself = self
    
    def _setup_ui(self):
        self._widget_d['filter_edit'] = QtGui.QLineEdit()
        self._widget_d['msg_level_combo'] = QtGui.QComboBox()
        self._widget_d['filter_btn'] = QtGui.QPushButton(_('Filter'))
        hlay = QtGui.QHBoxLayout()
        hlay.addWidget(self._widget_d['filter_edit'])
        hlay.addWidget(self._widget_d['msg_level_combo'])
        hlay.addWidget(self._widget_d['filter_btn'])
        
        self._widget_d['text_view'] = DebugTextView()
        lay = QtGui.QVBoxLayout()
        lay.addLayout(hlay)
        lay.addWidget(self._widget_d['text_view'])
        self.setLayout(lay)
        
        self.setWindowTitle(_('Debug'))
        self.resize(800, 600)
        
        
    def closeEvent(self, event):
        # pylint: disable=C0103
        logging.getLogger().removeHandler(self._widget_d['text_view'])
        event.ignore()
        
    
    def show(self):
        QtGui.QWidget.show(self)
        
    
    def __del__(self):
        print 'CLOSING DEBUG WINDOW'
        
        
        
        
        
        
class DebugTextView(QtGui.QTextEdit, logging.Handler):
    '''Debug messages visualization widget'''
    
    def __init__(self, parent=None):
        QtGui.QTextBrowser.__init__(self, parent)
        logging.Handler.__init__(self)
        self._list = []
        self._cursor = QtGui.QTextCursor(self.document())
        queue_handler = debugger.QueueHandler.get()
        for record in queue_handler.get_all():
            self.on_record_added(record)
        
    
    
    def emit(self, record):
        self.on_record_added(record)
        
        
        
    def handle(self, record):
        '''To send the handle message to logging.Handler base class
        instead of QTextEdit'''  
        logging.Handler.handle(self, record)
        
    def on_record_added(self, record):
        self._list.append(record)
        time_string = time.localtime(float(record.created))
        time_string = time.strftime("%H:%M:%S", time_string)
        html = u'<small>(%s): [<b>%s</b>] : %s</small><br />' % (
             time_string, record.name, record.msg.strip() )
        self._cursor.insertHtml(html)
