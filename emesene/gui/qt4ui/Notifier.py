# -*- coding: utf-8 -*-

'''This module contains classes to represent the notifications.'''

import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

class Notifier (QtGui.QLabel):
    ''' Class representing the notifications '''
    # pylint: disable=W0612
    NAME = 'Notifier'
    DESCRIPTION = 'The notifier to notify the notified user :)'
    AUTHOR = 'Gabriele Whisky Visconti'
    WEBSITE = ''
    # pylint: enable=W0612
    
    def __init__(self, title, text, uri):
        QtGui.QLabel.__init__(self, title+text+uri)


