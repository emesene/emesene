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
    NAME = 'MainPage'
    DESCRIPTION = 'The widget used to to display contact\'s info in ' \
                  'the conversation widget'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''
    # pylint: enable=W0612
    
    def __init__(self, parent=None):
        '''Constructor'''
        QtGui.QWidget.__init__(self, parent)
        self._emblem_lbl        = QtGui.QLabel()
        self._display_name_lbl  = QtGui.QLabel()
        self._message_lbl       = QtGui.QLabel()
        
        lay = QtGui.QGridLayout()
        lay.addWidget(self._emblem_lbl,         0, 0)
        lay.addWidget(self._display_name_lbl,   0, 1)
        lay.addWidget(self._message_lbl,        1, 1)
        lay.setColumnStretch(0, 0)
        lay.setColumnStretch(1, 1)
        self.setLayout(lay)
        
        self._display_name_lbl.setTextFormat(Qt.RichText)
        

    def update(self, status, display_name, message, account):
        '''Updates the infos shown in the panel'''
        print '1'
        pixmap          = QtGui.QPixmap(gui.theme.status_icons[status])
        print '2'
        #display_name    = Utils.escape(display_name)
        print '3'
        display_name    = Utils.parse_emotes(unicode(display_name + 
                                                 u'&nbsp;&nbsp;&nbsp;&nbsp;' \
                                                 u'[' + account + u']'))
        print '4'
        #message         = Utils.escape(message)
        print '5'
        message         = Utils.parse_emotes(unicode(message))
        print '6'
        
        self._emblem_lbl.setPixmap(pixmap)
        print '7'
        self._display_name_lbl.setText(display_name)
        print '8'
        self._message_lbl.setText(message)
        print '9'
        
    def update_icon(self, icon):
        '''Updates the icon'''
        pixmap = QtGui.QPixmap(icon)
        self._emblem_lbl.setPixmap(pixmap)
        
    def update_nick(self, nick):
        '''Updates the nick'''
        self._display_name_lbl.setText(Utils.escape(nick))
        
