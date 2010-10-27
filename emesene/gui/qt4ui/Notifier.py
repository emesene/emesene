# -*- coding: utf-8 -*-

'''This module contains classes to represent the notifications. At the moment 
this class is just a placeholder.'''

import PyQt4.QtGui      as QtGui

class Notifier (QtGui.QLabel):
    ''' Class representing the notifications '''
    # pylint: disable=W0612
    NAME = 'Notifier'
    DESCRIPTION = 'The notifier to notify the notified user :)'
    AUTHOR = 'Gabriele Whisky Visconti'
    WEBSITE = ''
    # pylint: enable=W0612
    
    def __init__(self, title, text, uri):
        QtGui.QLabel.__init__(self, unicode(title) + 
                                    unicode(text)  +
                                    unicode(uri)    )
                                    
        print (unicode(title) + 
               unicode(text)  +
               unicode(uri)    )
        self.show()


