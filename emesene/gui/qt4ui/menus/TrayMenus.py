# -*- coding: utf-8 -*-

'''This module contains menu widgets' classes'''

import PyQt4.QtGui      as QtGui

import extension

ICON = QtGui.QIcon.fromTheme

class TrayMainMenu (QtGui.QMenu):
    '''Tray's context menu, shown when main window is shown'''
    # pylint: disable=W0612
    NAME = 'Tray Main Menu'
    DESCRIPTION = 'The Main Menu of the tray icon'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''
    # pylint: enable=W0612
    
    def __init__(self, handler, parent=None):
        '''Constructor'''
        QtGui.QMenu.__init__(self, 'emesene2', parent)
        
        self._handler = handler

        status_menu_cls = extension.get_default('menu status')
        
        self.hide_show_mainwindow = QtGui.QAction(_('Hide/Show emesene'), self)
        self.status_menu = status_menu_cls(handler.on_status_selected)
        #self.list_contacts_menu = ContactsMenu(handler, main_window)
        self.disconnect = QtGui.QAction(ICON('network-disconnect'),
                                        _('Disconnect'), self)
        self.quit = QtGui.QAction(ICON('application-exit'),
                                 _('Quit'), self)
        

        self.addAction(self.hide_show_mainwindow)
        self.addMenu(self.status_menu)
        #self.addMenu(self.list_contacts_menu)        
        self.addAction(self.disconnect)
        self.addSeparator()
        self.addAction(self.quit)
        
        self.disconnect.triggered.connect(
            lambda *args: self._handler.on_disconnect_selected())
        self.quit.triggered.connect(
            lambda *args: self._handler.on_quit_selected())
            
            



class TrayLoginMenu (QtGui.QMenu):
    '''a widget that represents the menu displayed 
    on the trayicon on the login window'''

    def __init__(self, handler, parent=None):
        '''
        constructor

        handler -- a e3common.Handler.TrayIconHandler object
        '''
        QtGui.QMenu.__init__(self, parent)
        self._handler = handler
        self.hide_show_mainwindow = QtGui.QAction(_('Hide/Show emesene'), self)
        self.quit = QtGui.QAction(ICON('application-exit'), _('Quit'), self)
            
        self.addAction(self.hide_show_mainwindow)
        self.addSeparator()
        self.addAction(self.quit)

        self.quit.triggered.connect(
            lambda *args: self._handler.on_quit_selected())
