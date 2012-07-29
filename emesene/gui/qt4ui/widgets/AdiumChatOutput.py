# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''This module contains the AdiumChatOutput class'''
import base64
import xml

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import QtWebKit

import gui
from gui.qt4ui import Utils
from gui.base import Plus


class AdiumChatOutput (QtGui.QScrollArea, gui.base.OutputBase):
    '''A widget which displays various messages of a conversation
    using Adium themes'''
    NAME = 'AdiumChatOutput'
    DESCRIPTION = _('A widget to display conversation messages using adium style')
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    search_request = QtCore.pyqtSignal(basestring)

    #FIXME: implement custom context menu and steal emoticon option

    def __init__(self, config, parent=None):
        QtGui.QScrollArea.__init__(self, parent)
        gui.base.OutputBase.__init__(self, config)
        self.theme = gui.theme.conv_theme
        self._qwebview = QtWebKit.QWebView(self)

        self.setWidget(self._qwebview)
        self.setWidgetResizable(True)
        settings = self._qwebview.page().settings()
        settings.setFontSize(QtWebKit.QWebSettings.DefaultFontSize, 8)
        self._qwebview.setRenderHints(QtGui.QPainter.SmoothPixmapTransform)
        self._qwebview.page().setLinkDelegationPolicy(
                                    QtWebKit.QWebPage.DelegateAllLinks)
        self.clear()
        self._qwebview.loadFinished.connect(self._loading_finished_cb)
        self._qwebview.linkClicked.connect(self.on_link_clicked)

    def _loading_finished_cb(self, ok):
        self.ready = True

        for function in self.pending:
            self.add_message(function, self.config.b_allow_auto_scroll)
        self.pending = []

    def on_link_clicked(self, url):
        '''callback called when a link is clicked'''
        href = unicode(url.toString())
        if href.startswith("search://"):
            self.search_request.emit(href)
            return True

        if not href.startswith("file://"):
            gui.base.Desktop.open(href)
            return True

        return False

    def clear(self, source="", target="", target_display="",
            source_img="", target_img=""):
        '''clear the content'''
        body = self.theme.get_body(source, target, target_display, source_img,
                target_img)
        url = QtCore.QUrl(Utils.path_to_url(self.theme.path))
        self._qwebview.setHtml(body, url)
        self.pending = []
        self.ready = False

    def add_message(self, msg, scroll):
        '''add a message to the conversation'''
        if msg.type == "status":
            msg.message = Plus.msnplus_strip(msg.message)
        html = self.theme.format(msg, scroll)
        self._qwebview.page().mainFrame().evaluateJavaScript(html)

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

