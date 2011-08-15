# -*- coding: utf-8 -*-

'''This module contains the AdiumChatOutput class'''
import base64
import webbrowser

from PyQt4      import QtGui
from PyQt4      import QtCore
from PyQt4      import QtWebKit

import e3
import gui
from gui.base import Plus
from gui.qt4ui  import Utils
from gui.qt4ui.Utils import tr


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
        
        self.theme = gui.theme.conv_theme
        self.last_incoming = None
        self.last_incoming_account = None
        self.last_incoming_nickname = None

        self._qwebview = QtWebKit.QWebView(self)
        self._last_sender = None
        
        self.setWidget(self._qwebview)
        self.setWidgetResizable(True)
        self._qwebview.setRenderHints(QtGui.QPainter.SmoothPixmapTransform)
        self._qwebview.page().setLinkDelegationPolicy(
                                    QtWebKit.QWebPage.DelegateAllLinks)
        
        pic = gui.theme.image_theme.user
        body = gui.theme.conv_theme.get_body('', '', '', pic, pic)
        self._qwebview.setHtml(body)
        
        self._qwebview.linkClicked.connect(
                        lambda qt_url: webbrowser.open(qt_url.toString()) )
                            
    def _append_message(self, msg, style=None, cedict={}, cedir=None):
        '''add a message to the conversation'''

        b_nick_check = bool(self.last_incoming_nickname != msg.display_name)
        if b_nick_check:
            self.last_incoming_nickname = msg.display_name

        if msg.incoming:
            if self.last_incoming is None:
                self.last_incoming = False

            msg.first = not self.last_incoming

            if self.last_incoming_account != msg.sender or b_nick_check:
                msg.first = True

            html = self.theme.format_incoming(msg, style, cedict, cedir)
            self.last_incoming = True
            self.last_incoming_account = msg.sender
        else:
            if self.last_incoming is None:
                self.last_incoming = True

            msg.first = self.last_incoming

            html = self.theme.format_outgoing(msg, style, cedict, cedir)
            self.last_incoming = False

        if msg.type == "status":
            self.last_incoming = None
            msg.first = True

        if msg.first:
            function = "appendMessage('" + html + "')"
        else:
            function = "appendNextMessage('" + html + "')"

        self._qwebview.page().mainFrame().evaluateJavaScript(function)

    def send_message(self, formatter, contact, message, cedict, cedir, is_first):
        '''add a message to the widget'''
        msg = gui.Message.from_contact(contact, message, is_first, False, message.timestamp)
        self._append_message(msg, message.style, cedict, cedir)

    def receive_message(self, formatter, contact, message, cedict, cedir, is_first):
        '''add a message to the widget'''
        msg = gui.Message.from_contact(contact, message, is_first, True, message.timestamp)
        self._append_message(msg, message.style, cedict, cedir)

    def information(self, formatter, contact, message):
        '''add an information message to the widget'''
        msg = gui.Message.from_information(contact, message)
        msg.message = Plus.msnplus_strip(msg.message)
        self._append_message(msg, None, None, None)

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
        
        
        
        
        
