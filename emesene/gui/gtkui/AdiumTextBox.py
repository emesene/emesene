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

import os
import gtk
import urllib
import logging
log = logging.getLogger('gtkui.AdiumTextBox')
import webkit
import base64
import xml.sax.saxutils

import webbrowser

import e3
import gui
import Renderers

class OutputView(webkit.WebView):
    '''a class that represents the output widget of a conversation
    '''

    def __init__(self, theme, source, target, target_display, source_img,
            target_img):
        webkit.WebView.__init__(self)
        # Trying to debug issue #232
        # https://github.com/emesene/emesene/issues/#issue/232
        webkit_settings = self.get_settings()
        webkit_settings.set_property("enable-plugins", False)

        self.theme = theme
        self.last_incoming = None
        self.last_incoming_account = None
        self.ready = False
        self.pending = []
        self.connect('load-finished', self._loading_finished_cb)
        self.connect('populate-popup', self.on_populate_popup)
        self.connect("navigation-requested", self.on_navigation_requested)


    def _loading_finished_cb(self, *args):
        '''callback called when the content finished loading
        '''
        self.ready = True

        for function in self.pending:
            self.execute_script(function)
        if self.pending:
            self.execute_script("scrollToBottom()")
        self.pending = []

    def clear(self, source="", target="", target_display="",
            source_img="", target_img=""):
        '''clear the content'''
        body = self.theme.get_body(source, target, target_display, source_img,
                target_img)
        self.load_string(body,
                "text/html", "utf-8", path_to_url(self.theme.path))
        self.pending = []
        self.ready = False

    def add_message(self, msg, style=None, cedict={}, cedir=None):
        '''add a message to the conversation'''

        if msg.incoming:
            if self.last_incoming is None:
                self.last_incoming = False

            msg.first = not self.last_incoming

            if self.last_incoming_account != msg.sender:
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

        if msg.first:
            function = "appendMessage('" + html + "')"
        else:
            function = "appendNextMessage('" + html + "')"


        self.append(function)

    def append(self, function):
        '''append a message if the renderer finished loading, append it to
        pending if still loading
        '''
        if self.ready:
            self.execute_script(function)
            self.execute_script("scrollToBottom()")
        else:
            self.pending.append(function)

    def _set_text(self, text):
        '''set the text on the widget'''
        self._textbox.load_string(text, "text/html", "utf-8", "")
        self.pending = []
        self.ready = False

    def _get_text(self):
        '''return the text of the widget'''
        self._textbox.execute_script('oldtitle=document.title;document.title=document.documentElement.innerHTML;')
        html = self._textbox.get_main_frame().get_title()
        self._textbox.execute_script('document.title=oldtitle;')
        return html

    text = property(fget=_get_text, fset=_set_text)

    def on_populate_popup(self, view, menu):
        '''disables the right-click menu by removing the MenuItems'''
        for child in menu.get_children():
            menu.remove(child)

    def on_navigation_requested(self, widget, WebKitWebFrame, WebKitNetworkRequest):
        '''callback called when a link is clicked'''
        href = WebKitNetworkRequest.get_uri()

        if not href.startswith("file://"):
            log.info("link clicked: " + href)
            webbrowser.open_new_tab(href)
            return True

        return False


class OutputText(gtk.ScrolledWindow):
    '''a text box inside a scroll that provides methods to get and set the
    text in the widget'''
    NAME = 'Adium Output'
    DESCRIPTION = _('A widget to display conversation messages using adium style')
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, config):
        '''constructor'''
        gtk.ScrolledWindow.__init__(self)

        self.config = config

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_IN)
        self._texts = []
        self.loaded = False
        picture = path_to_url(os.path.abspath(gui.theme.user))

        self.view = OutputView(gui.theme.conv_theme, "", "", "", picture,
                picture)
        self.view.connect('load-finished', self._loading_stop_cb)
        self.view.connect('console-message', self._error_cb)
        self.clear()
        self.view.show()
        self.add(self.view)

    def clear(self, source="", target="", target_display="",
            source_img="", target_img=""):
        '''clear the content'''
        self._texts = []
        self.loaded = False
        self.view.clear(source, Renderers.msnplus_to_plain_text(target), Renderers.msnplus_to_plain_text(target_display),
            source_img, target_img)

    def _error_cb(self, view, message, line, source_id):
        '''called when a message is sent to the console'''
        message = "Webkit message: %s %s %s" % (message, line, source_id)
        log.debug(message)

    def _loading_stop_cb(self, view, frame):
        '''method called when the page finish loading'''
        self.loaded = True
        for text in self._texts:
            self.append(text)

        self._texts = []

    def send_message(self, formatter, contact, text, cedict, cedir, style, is_first, type_=None):
        '''add a message to the widget'''
        if type_ is e3.Message.TYPE_NUDGE:
            text = _('You just sent a nudge!')

        msg = gui.Message.from_contact(contact, text, is_first, False)
        self.view.add_message(msg, style, cedict, cedir)

    def receive_message(self, formatter, contact, message, cedict, cedir, is_first):
        '''add a message to the widget'''
        msg = gui.Message.from_contact(contact, message.body, is_first, True, message.timestamp)
        self.view.add_message(msg, message.style, cedict, cedir)

    def information(self, formatter, contact, message):
        '''add an information message to the widget'''
        # TODO: make it with a status message
        msg = gui.Message.from_contact(contact, message, False, True)
        self.view.add_message(msg, None, None, None)

    def update_p2p(self, account, _type, *what):
        ''' new p2p data has been received (custom emoticons) '''
        if _type == 'emoticon':
            _creator, _friendly, path = what
            _id = base64.b64encode(_creator+xml.sax.saxutils.unescape(_friendly)) #see gui/base/MarkupParser.py
            mystr = "var now=new Date();var x=document.images;for(var i=0;i<x.length;i++){if(x[i].name=='%s'){x[i].src='%s?'+now.getTime();}}" % (_id, path)
            self.view.execute_script(mystr)

def path_to_url(path):
    if os.name == "nt":
        # on windows os.path.join uses backslashes
        path = path.replace("\\", "/")
        path = path[2:]

    path = urllib.quote(path)
    path = "file://" + path

    return path
