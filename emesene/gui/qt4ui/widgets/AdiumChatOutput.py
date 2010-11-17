# -*- coding: utf-8 -*-

'''This module contains the AdiumChatOutput class'''

from PyQt4      import QtGui
from PyQt4      import QtCore
from PyQt4      import QtWebKit

import e3
import gui

from gui.qt4ui  import Utils


class AdiumChatOutput (QtGui.QScrollArea):
    '''A widget which displays various messages of a conversation 
    using Adium themes'''
    # pylint: disable=W0612
    NAME = 'AdiumChatOutput'
    DESCRIPTION = 'A widget to display conversation messages with Adium' \
                  'themes. Based on Webkit technology.'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''
    # pylint: enable=W0612
    
    def __init__(self, parent=None):
        QtGui.QScrollArea.__init__(self, parent)
        self._qwebview = QtWebKit.QWebView(self)
        
        self.setWidget(self._qwebview)
        self.setWidgetResizable(True)
        self._qwebview.setHtml(
                            gui.theme.conv_theme.get_body('', '', '', '', ''))
                            
    def send_message(self, formatter, contact, text, cedict, cedir, style, is_first, type_=None):
        '''add a message to the widget'''
        if type_ is e3.Message.TYPE_NUDGE:
            text = _('You just sent a nudge!')

        msg = gui.Message.from_contact(contact, text, is_first, False)
        #self.view.add_message(msg, style, cedict, cedir)
        msg.first = True
        html = gui.theme.conv_theme.format_outgoing(msg, style, cedict, cedir)
        function = "appendMessage('" + html + "')"
        self._qwebview.page().mainFrame().evaluateJavaScript(function)
        
    def receive_message(self, formatter, contact, message, cedict, cedir, is_first):
        '''add a message to the widget'''
        msg = gui.Message.from_contact(contact, message.body, is_first, True, message.timestamp)
        # WARNING: this is a hack to keep out config from backend libraries
        #message.style.size = self.config.i_font_size
        msg.first = True
        html = gui.theme.conv_theme.format_incoming(msg, message.style, cedict, cedir)
        function = "appendMessage('" + html + "')"
        self._qwebview.page().mainFrame().evaluateJavaScript(function)
        
        
        
        
        
