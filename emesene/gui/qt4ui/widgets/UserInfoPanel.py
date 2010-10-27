# -*- coding: utf-8 -*-

'''This module contains the UserInfoPanel class.'''

import PyQt4.QtGui      as QtGui

import gui


class UserInfoPanel (QtGui.QLabel):
    '''This class represents a label widget showing
    other contact's info in a conversation window'''
    
    def __init__(self, parent=None):
        '''Constructor'''
        QtGui.QLabel.__init__(self, parent)
        self._text_skeleton = \
            '''<table>
                <tr>    
                    <td><img src="%s"></td>
                    <td>%s [%s]</td>
                </tr>
                <tr>
                    <td></td>
                    <td><font><i>%s</i></font></td>
                </tr>
            <table>'''

    def update(self, status, nick, message, account):
        '''Updates the infos shown in the panel'''
        text = self._text_skeleton % (
                        gui.theme.status_icons[status],
                        unicode(nick),
                        account,
                        unicode(message))
        self.setText(text)
        
