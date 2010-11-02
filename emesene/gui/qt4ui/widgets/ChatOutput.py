# -*- coding: utf-8 -*-

'''This module contains the ChatTextEdit class'''

import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore

import e3

from gui.qt4ui  import Utils


class ChatOutput (QtGui.QTextBrowser):
    '''A widget which displays various messages of a conversation'''
    # pylint: disable=W0612
    NAME = 'MainPage'
    DESCRIPTION = 'A widget to display the conversation messages'
    AUTHOR = 'Gabriele Whisky Visconti'
    WEBSITE = ''
    # pylint: enable=W0612
    
    def __init__(self, parent=None):
        '''Constructor'''
        QtGui.QTextBrowser.__init__(self, parent)
        self._chat_text = QtCore.QString('')
        
    
    # emesene's
    def receive_message(self, formatter, contact, 
                        message, cedict, cedir, first):
        '''This method is called from the core (e3 or base class or whatever
        when a new message arrives. It shows the new message'''
        print formatter,
        print contact,
        print message.type,
        print message.account
        print cedict,
        print first
        
        self._append_to_chat(
                Utils.parse_emotes(u'<b>' + contact.display_name + u':</b>'))
        self._append_to_chat(
                Utils.parse_emotes(Utils.escape(unicode(message.body))),
                message.style)
        self._append_to_chat('<br>')
            
            
    # emesene's
    def send_message(self, formatter, my_account,
                     text, cedict, cedir, cstyle, first):
        '''This method is called from the core, when a message is sent by us.
        It shows the message'''
        self._append_to_chat('<b>ME:</b>')
        self._append_to_chat(Utils.parse_emotes(Utils.escape(unicode(text))), 
                             cstyle)
        self._append_to_chat('<br/>')
        
    
    # emesene's                         
    def information(self, formatter, contact, message):
        '''This method is called by the core, when there's the need to display 
        an information message'''
        self._append_to_chat(Utils.parse_emotes('<p align="right"><i>' + 
                             Utils.escape(unicode(message)) + 
                             '</i></p>'))
                             
                             
    def _append_to_chat(self, html_string, cstyle=None):
        '''Method that appends an html string to the chat view'''
        vert_scroll_bar = self.verticalScrollBar()
        position = vert_scroll_bar.value()
        if position == vert_scroll_bar.maximum():
            at_bottom = True
        else:
            at_bottom = False
         
        if cstyle:
            html_string = e3.common.add_style_to_message(html_string, 
                                                         cstyle, False)

        self._chat_text.append(html_string)
        self.setText(self._chat_text)

        if at_bottom:
            vert_scroll_bar.setValue(vert_scroll_bar.maximum())
        else:
            vert_scroll_bar.setValue(position)
