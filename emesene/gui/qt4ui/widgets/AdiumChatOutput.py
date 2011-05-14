# -*- coding: utf-8 -*-

'''This module contains the AdiumChatOutput class'''
import base64

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
        self._qwebview.setRenderHints(QtGui.QPainter.SmoothPixmapTransform)
        self._last_sender = None
        
        self.setWidget(self._qwebview)
        self.setWidgetResizable(True)
        pic = gui.theme.user
        body = gui.theme.conv_theme.get_body('', '', '', pic, pic)
        self._qwebview.setHtml(body)
                            
                            
    def _append_message(self, contact, message, cedict,
                        cedir, is_incoming, timestamp=None):
        
        msg = gui.Message.from_contact(contact, message.body, first=True,
                                       incomming=is_incoming, tstamp=timestamp)
        if msg.sender != self._last_sender:
            function = "appendMessage('%s')"
            msg.first = True
            self._last_sender = msg.sender
        else:
            function = "appendNextMessage('%s')"
            msg.first = False
            
        if is_incoming:
            html = gui.theme.conv_theme.format_incoming(msg, message.style, 
                                                        cedict, cedir)
        else:
            html = gui.theme.conv_theme.format_outgoing(msg, message.style, 
                                                        cedict, cedir)
            
        self._qwebview.page().mainFrame().evaluateJavaScript(function % html)
                            

    def information(self, formatter, contact, message):
        '''add an information message to the widget'''
        # TODO: make it with a status message
        self._append_message(contact, message, cedict={}, 
                             cedir='', style=None, is_incoming=True)
        
        
    def send_message(self, formatter, contact, message, 
                     cedict, cedir, is_first):
        '''add a message to the widget'''
        if message.type is e3.Message.TYPE_NUDGE:
            message.body = _('You just sent a nudge!')        
        self._append_message(contact, message, cedict, 
                             cedir, is_incoming=False)
        
        
    def receive_message(self, formatter, contact, 
                        message, cedict, cedir, is_first):
        '''add a message to the widget'''
        # WARNING: this is a hack to keep out config from backend libraries
        #message.style.size = self.config.i_font_size
        self._append_message(contact, message, cedict, cedir, 
                             is_incoming=True, 
                             timestamp=message.timestamp)

        
    def update_p2p(self, account, _type, *what):
        ''' new p2p data has been received (custom emoticons) '''
        if _type == 'emoticon':
            _creator, _friendly, path = what
            _friendly = xml.sax.saxutils.unescape(_friendly)
            #see gui/base/MarkupParser.py:
            _id = base64.b64encode(_creator + _friendly) 
            mystr = '''
                        var now=new Date();
                        var x=document.images;
                        for (var i=0; i<x.length; i++){
                            if (x[i].name=='%s') {
                                x[i].src='%s?'+now.getTime();
                            }
                       }''' % (_id, path)
            self._qwebview.page().mainFrame().evaluateJavaScript(mystr)
        
        
        
        
        
