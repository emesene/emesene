# -*- coding: utf-8 -*-

'''This module contains the UserInfoPanel class.'''

import PyQt4.QtGui      as QtGui
from PyQt4.QtCore   import Qt


import gui
from gui.qt4ui import Utils


class UserInfoPanel (QtGui.QWidget):
    '''This class represents a label widget showing
    other contact's info in a conversation window'''
    # pylint: disable=W0612
    NAME = 'Header'
    DESCRIPTION = 'The widget used to to display contact\'s info in ' \
                  'the conversation widget'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''
    # pylint: enable=W0612
    
    def __init__(self, parent=None):
        '''Constructor'''
        QtGui.QWidget.__init__(self, parent)
        
        self._account = ''
        self._message_lbl       = QtGui.QLabel()
        
        lay = QtGui.QHBoxLayout()
        lay.addWidget(self._message_lbl)
        self.setLayout(lay)
        self._message_lbl.setTextFormat(Qt.RichText)
        

    def set_all(self, message, account):
        '''Updates the infos shown in the panel'''
        self._account = account
        self.set_message(message)
        
    def set_icon(self, icon):
        '''Updates the icon'''
        pixmap = QtGui.QPixmap(icon)
        self._emblem_lbl.setPixmap(pixmap)
        
    def set_message(self, message):
        '''Updates the message'''
        message = Utils.escape(message)
        message = Utils.parse_emotes(unicode(message))
        message = message + (u'<br /><span style="font-size: small;">[%s]</span>' % self._account)
        self._message_lbl.setText(message)
        
        
