# -*- coding: utf-8 -*-

''' This module contains the tray icon's class'''

import PyQt4.QtGui as QtGui

class TrayIcon (QtGui.QWidget):
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
        QtGui.QWidget.__init__(self)
        self.handler = handler
        self.main_window = main_window
        self.c = None
        
    def set_conversations(self, conversations): # emesene's
        print "Tray Icon: %s" % conversations
        
        self.c = conversations 
        
        

    def set_login(self):
        '''does nothing'''
        pass

    def set_main(self, session):
        '''does nothing'''
        pass
