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
import logging
log = logging.getLogger('gtkui.AdiumTextBox')
import webkit
import base64
import xml.sax.saxutils

import webbrowser

import e3
import gui
from gui.base import Plus
import utils

class OutputView(webkit.WebView):
    '''a class that represents the output widget of a conversation
    '''

    def __init__(self, theme, source, target, target_display, source_img,
            target_img, add_emoticon_cb):
        webkit.WebView.__init__(self)
        # Trying to debug issue #232
        # https://github.com/emesene/emesene/issues/#issue/232
        webkit_settings = self.get_settings()
        webkit_settings.set_property("enable-plugins", False)

        self.theme = theme
        self.last_incoming = None
        self.last_incoming_account = None
        self.last_incoming_nickname = None
        self.ready = False
        self.pending = []
        self.add_emoticon_cb = add_emoticon_cb
        self.connect('load-finished', self._loading_finished_cb)
        self.connect('populate-popup', self.on_populate_popup)
        self.connect('navigation-requested', self.on_navigation_requested)
        self.connect('download-requested', self.on_download_requested)

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
                "text/html", "utf-8", utils.path_to_url(self.theme.path))
        self.pending = []
        self.ready = False
        self.last_incoming = None

    def add_message(self, msg, style=None, cedict={}, cedir=None):
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
        self.load_string(text, "text/html", "utf-8", "")
        self.pending = []
        self.ready = False

    def _get_text(self):
        '''return the text of the widget'''
        self.execute_script('oldtitle=document.title;document.title=document.documentElement.innerHTML;')
        html = self.get_main_frame().get_title()
        self.execute_script('document.title=oldtitle;')
        return html

    text = property(fget=_get_text, fset=_set_text)

    def on_populate_popup(self, view, menu):
        '''disables the right-click menu by removing the MenuItems'''
        children = menu.get_children()
        for i, child in enumerate(children):
            # Ditry hack. The first 3 buttons of the non-image menu
            # are insensitive
            if i == 1 and child.get_property('sensitive'):
                child.set_use_stock(False)
                child.set_property("label", _("Save"))
            else:
                menu.remove(child)
                child.destroy()

        select_all_item = gtk.MenuItem(label=_("Select All"))
        select_all_item.connect('activate', lambda *args: self.select_all())
        clear_item = gtk.MenuItem(label=_("Clear"))
        clear_item.connect('activate', self.clear)
        menu.append(select_all_item)
        menu.append(clear_item)
        menu.show_all()

    def on_download_requested(self, webview, download):
        if self.add_emoticon_cb is not None:
            self.add_emoticon_cb(download.get_uri())
        return False

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

    def __init__(self, config, add_emoticon_cb):
        '''constructor'''
        gtk.ScrolledWindow.__init__(self)

        self.config = config

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_IN)
        self.loaded = False
        picture = utils.path_to_url(os.path.abspath(gui.theme.image_theme.user))

        self.view = OutputView(gui.theme.conv_theme, "", "", "", picture,
                picture, add_emoticon_cb)
        self.view.connect('console-message', self._error_cb)
        self.clear()
        self.view.show()
        self.add(self.view)

    def clear(self, source="", target="", target_display="",
            source_img="", target_img=""):
        '''clear the content'''
        self.view.clear(source, target, target_display, source_img, target_img)

    def _error_cb(self, view, message, line, source_id):
        '''called when a message is sent to the console'''
        message = "Webkit message: %s %s %s" % (message, line, source_id)
        log.debug(message)

    def send_message(self, formatter, contact, message, cedict, cedir, is_first):
        '''add a message to the widget'''
        msg = gui.Message.from_contact(contact, message, is_first, False, message.timestamp)
        self.view.add_message(msg, message.style, cedict, cedir)

    def receive_message(self, formatter, contact, message, cedict, cedir, is_first):
        '''add a message to the widget'''
        msg = gui.Message.from_contact(contact, message, is_first, True, message.timestamp)
        self.view.add_message(msg, message.style, cedict, cedir)

    def information(self, formatter, contact, message):
        '''add an information message to the widget'''
        msg = gui.Message.from_information(contact, message)
        msg.message = Plus.msnplus_strip(msg.message)
        self.view.add_message(msg, None, None, None)

    def update_p2p(self, account, _type, *what):
        ''' new p2p data has been received (custom emoticons) '''
        if _type == 'emoticon':
            _creator, _friendly, path = what
            _id = base64.b64encode(_creator+xml.sax.saxutils.unescape(_friendly)) #see gui/base/MarkupParser.py
            mystr = "var now=new Date();var x=document.images;for(var i=0;i<x.length;i++){if(x[i].name=='%s'){x[i].src='%s?'+now.getTime();}}" % (_id, path)
            self.view.execute_script(mystr)
