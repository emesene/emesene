# -*- coding: utf-8 -*-

''' This module contains the tray icon's class'''

class TrayIcon(object):
    '''A class that implements the tray icon of emesene for KDE4'''
    # pylint: disable=W0612
    NAME = 'MainWindow'
    DESCRIPTION = 'KDE4 Tray Icon'
    AUTHOR = 'Gabriele Whisky Visconti'
    WEBSITE = ''
    # pylint: enable=W0612

    def __init__(self, handler, main_window=None):
        '''
        constructor

        handler -- a e3common.Handler.TrayIconHandler object
        '''
        pass

    def set_login(self):
        '''does nothing'''
        pass

    def set_main(self, session):
        '''does nothing'''
        pass
