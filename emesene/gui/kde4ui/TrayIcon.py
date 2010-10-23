# -*- coding: utf-8 -*-

''' This module contains the tray icon's class'''

import PyKDE4.kdeui     as KdeGui
from PyKDE4.kdecore import i18n
import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

import gui
import e3

class TrayIcon (KdeGui.KStatusNotifierItem):
    '''A class that implements the tray icon of emesene for KDE4'''
    # pylint: disable=W0612
    NAME = 'TrayIcon'
    DESCRIPTION = 'KDE4 Tray Icon'
    AUTHOR = 'Gabriele Whisky Visconti'
    WEBSITE = ''
    # pylint: enable=W0612

    def __init__(self, handler, main_window=None):
        '''
        constructor

        handler -- a e3common.Handler.TrayIconHandler object
        '''
        KdeGui.KStatusNotifierItem.__init__(self)
        
        self._handler = handler
        self._main_window = main_window
        self._conversations = None
        
        self.setStatus(KdeGui.KStatusNotifierItem.Active)
        self.setIconByPixmap(QtGui.QIcon(
                             QtGui.QPixmap(
                             gui.theme.logo).scaled(QtCore.QSize(40, 40))))
                             
        self.activateRequested.connect(self._on_tray_icon_clicked)
                            
        
    
        
        

    def set_login(self):
        '''does nothing'''
        pass

    def set_main(self, session):
        '''does nothing'''
        self._handler.session = session
        self._handler.session.signals.status_change_succeed.subscribe(
                                            self._on_status_changed)
        
        

    def set_conversations(self, conversations): # emesene's
        '''Stores a reference to the conversation page'''
        self._conversations = conversations 
        
        
        
    def _on_status_changed(self, status):
        self.setIconByPixmap(QtGui.QIcon(QtGui.QPixmap(gui.theme.status_icons_panel[status])))
        
        
    def _on_tray_icon_clicked(self, active, pos):
        if not self._main_window:
            return 
            
        if not self._main_window.isVisible():
            self._main_window.show()
            self._main_window.activateWindow()
            self._main_window.raise_()
        else: # visible
            if self._main_window.isActiveWindow():
                self._main_window.hide()
            else:
                self._main_window.activateWindow()
                self._main_window.raise_()
        
        
        
        
        
