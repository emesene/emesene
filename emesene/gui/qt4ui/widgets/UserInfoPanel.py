# -*- coding: utf-8 -*-

'''This module contains the UserInfoPanel class.'''

import PyQt4.QtGui      as QtGui

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

    def update(self, status, display_name, message, account):
        '''Updates the infos shown in the panel'''
        pixmap          = QtGui.QPixmap(gui.theme.status_icons[status])
        #display_name    = Utils.escape(display_name)
        display_name    = Utils.parse_emotes(unicode(display_name + 
                                                 u'&nbsp;&nbsp;&nbsp;&nbsp;' \
                                                 u'[' + account + u']'))
        #message         = Utils.escape(message)
        message         = Utils.parse_emotes(unicode(message))
        
        self._emblem_lbl.setPixmap(pixmap)
        self._display_name_lbl.setText(display_name)
        self._message_lbl.setText(message)
        
        
