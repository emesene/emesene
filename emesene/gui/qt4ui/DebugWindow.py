# -*- coding: utf-8 -*-

'''This module contains classes needed to the debug window'''

import logging
import time

from PyQt4  import QtGui

from gui.qt4ui import Utils
from gui.qt4ui.Utils import tr

import debugger


log = logging.getLogger('qt4ui.DebugWindow')

class DebugWindow(QtGui.QWidget):
    '''A Window which shows debug messages'''
    NAME = 'Debug Window'
    DESCRIPTION = 'A window which shows debug messages'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    def __init__(self, on_close_cb, parent=None):
        '''Constructor'''
        QtGui.QWidget.__init__(self, parent)
        self._on_close_cb = on_close_cb
        self._widget_d = {}
        self._setup_ui()
        logging.getLogger().addHandler(self._widget_d['text_view'])
        
        
    def _setup_ui(self):
        '''Instantiates the widgets, and sets the layout'''
        widget_d = self._widget_d
        widget_d['filter_edit'] = QtGui.QLineEdit()
        widget_d['msg_level_combo'] = QtGui.QComboBox()
        widget_d['filter_btn'] = QtGui.QPushButton(tr('Filter'))
        hlay = QtGui.QHBoxLayout()
        hlay.addWidget(widget_d['filter_edit'])
        hlay.addWidget(widget_d['msg_level_combo'])
        hlay.addWidget(widget_d['filter_btn'])
        
        widget_d['text_view'] = DebugTextView()
        lay = QtGui.QVBoxLayout()
        lay.addLayout(hlay)
        lay.addWidget(widget_d['text_view'])
        self.setLayout(lay)
        
        combo = widget_d['msg_level_combo']
        combo.addItem('Debug'   , logging.DEBUG   )
        combo.addItem('Info'    , logging.INFO    )
        combo.addItem('Warning' , logging.WARNING )
        combo.addItem('Error'   , logging.ERROR   )
        combo.addItem('Critical', logging.CRITICAL)
        self.setWindowTitle(tr('Debug'))
        self.resize(800, 600)
        
        combo.currentIndexChanged.connect(
                    lambda *args :self._on_filter_changed())
        widget_d['filter_btn'].clicked.connect(
                    lambda *args: self._on_filter_changed())
        widget_d['filter_edit'].returnPressed.connect(
                    lambda *args: self._on_filter_changed())
        
        
        
    def _on_filter_changed(self):
        '''Called when the user tries to set a new filter'''
        widget_d = self._widget_d
        i     = widget_d['msg_level_combo'].currentIndex()
        level = widget_d['msg_level_combo'].itemData(i).toPyObject()
        name  = widget_d['filter_edit'].text()
        new_filter = Filter(level, name)
        widget_d['text_view'].set_filter(new_filter)
       
         
        
    def closeEvent(self, event):
        '''Overrides base's class method'''
        # pylint: disable=C0103
        logging.getLogger().removeHandler(self._widget_d['text_view'])
        QtGui.QWidget.closeEvent(self, event)
        self._on_close_cb()
        #event.ignore()
        
    
    def show(self):
        '''Show the window'''
        QtGui.QWidget.show(self)
        
    
    def __del__(self):
        '''Destrusctor'''
        print 'CLOSING DEBUG WINDOW'
        self._on_close_cb()
        
        
        
        
        
class DebugTextView(QtGui.QTextEdit, logging.Handler):
    '''Debug messages visualization widget'''
    
    def __init__(self, filter=None, parent=None):
        '''Constructor'''
        QtGui.QTextBrowser.__init__(self, parent)
        logging.Handler.__init__(self)
        if not filter:
            filter = Filter(0, '')
        self._list = []
        self._filter = filter
        self.setReadOnly(True)
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
        '''This methos is called whenever we need to add a record'''
        self._list.append(record)
        if self._filter.is_matched_by(record):
            self._show_record(record)
            
    
    def set_filter(self, filter):
        '''Sets a new filter, and refilters, if needed'''
        refilter = False
        if (self._filter.name  != filter.name ) or \
             (self._filter.level != filter.level):
            refilter = True
        self._filter = filter
        if refilter:
            self._refilter()
            
        
    def _show_record(self, record):
        '''Appends a record in the view'''
        time_string = time.localtime(float(record.created))
        time_string = time.strftime("%H:%M:%S", time_string)
        html = u'<small>(%s): [<b>%s</b>] : '
        html = html % (time_string, record.name)
        try:
            html = html + '%s</small><br />' % Utils.escape(record.msg.strip())
        except AttributeError as detail:
            html = html + '<small><i>&lt;&lt;message insertion failed [%s:%s]&gt;&gt;</i></small><br>' % (type(record.msg), str(record.msg))
        self._cursor.insertHtml(html)
        
        
    def _refilter(self):
        '''Recalculates the view from scratch'''
        self._cursor.document().clear()
        for record in self._list:
            if self._filter.is_matched_by(record):
                self._show_record(record)
        
        
        
        
    
class Filter(object):
    '''Convenience class to represent a filter'''
    def __init__(self, level, name):
        '''Constructor'''
        self.level = level
        self.name = name
        
    def is_matched_by(self, record):
        '''Determines if the given record matches the given
        filter'''
        if record.levelno < self.level:
            return False
        if str(record.name).find(self.name) == -1:
            return False
        return True
        
