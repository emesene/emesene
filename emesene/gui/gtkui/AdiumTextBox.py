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

import gtk
import gobject
import logging
log = logging.getLogger('gtkui.AdiumTextBox')

#check for webkit gi package
from gui.gtkui import check_gtk3
try:
    if check_gtk3():
        import gi.pygtkcompat
        gi.pygtkcompat.enable_webkit(version='3.0')
except ValueError:
    raise ImportError

import webkit
import base64
import xml.sax.saxutils

import e3
import gui
from gui.base import Plus
import utils

class OutputView(webkit.WebView):
    '''a class that represents the output widget of a conversation
    '''
    __gsignals__ = {
            "search_request": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (gobject.TYPE_PYOBJECT,))
            }

    def __init__(self, theme, handler):
        webkit.WebView.__init__(self)
        settings = self.get_settings()
        settings.set_property('default-font-size', 8)

        self.handler = handler
        self.theme = theme
        self.ready = False
        self.pending = []
        self.connect('load-finished', self._loading_finished_cb)
        self.connect('populate-popup', self.on_populate_popup)
        self.connect('navigation-requested', self.on_navigation_requested)
        self.connect('download-requested', self.on_download_requested)
        self.connect('console-message', self._error_cb)

    def _loading_finished_cb(self, *args):
        '''callback called when the content finished loading
        '''
        self.ready = True

        for function in self.pending:
            self.execute_script(function)
        self.pending = []

    def _error_cb(self, view, message, line, source_id):
        '''called when a message is sent to the console'''
        message = "Webkit message: %s %s %s" % (message, line, source_id)
        log.debug(message)

    def clear(self, source="", target="", target_display="",
            source_img="", target_img=""):
        '''clear the content'''
        body = self.theme.get_body(source, target, target_display, source_img,
                target_img)
        self.load_string(body,
                "text/html", "utf-8", utils.path_to_url(self.theme.path))
        self.pending = []
        self.ready = False

    def add_message(self, msg, scroll=True):
        '''add a message to the conversation. append the message directly
        if the renderer finished loading, append it to
        pending if still loading'''

        function = self.theme.format(msg, scroll)

        if self.ready:
            gobject.idle_add(self.execute_script, function)
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
            if len(children) == 4:
                if i == 1 and child.get_property('sensitive'):
                    child.set_use_stock(False)
                    child.set_property("label", _("Save"))
                else:
                    menu.remove(child)
                    child.destroy()

        select_all_item = gtk.MenuItem(_("Select All"))
        select_all_item.connect('activate', lambda *args: self.select_all())
        menu.append(select_all_item)

        if self.handler is not None:
            clear_item = gtk.MenuItem(_("Clear"))
            clear_item.connect('activate',  lambda *args: self.handler.on_clean_selected())
            menu.append(clear_item)

        menu.show_all()

    def on_download_requested(self, webview, download):
        if self.handler is not None:
            uri = download.get_uri().split("?")[0]
            self.handler.add_emoticon_selected(uri)
        return False

    def on_navigation_requested(self, widget, WebKitWebFrame, WebKitNetworkRequest):
        '''callback called when a link is clicked'''
        href = WebKitNetworkRequest.get_uri()

        if href.startswith("search://"):
            self.emit("search_request", href)
            return True

        if not href.startswith("file://"):
            log.info("link clicked: " + href)
            gui.base.Desktop.open(href)
            return True

        return False


class OutputText(gui.base.OutputBase, gtk.ScrolledWindow):
    '''a text box inside a scroll that provides methods to get and set the
    text in the widget'''
    NAME = 'Adium Output'
    DESCRIPTION = _('A widget to display conversation messages using adium style')
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    __gsignals__ = {
            "search_request": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (gobject.TYPE_PYOBJECT,))
            }

    def __init__(self, config, handler):
        '''constructor'''
        gtk.ScrolledWindow.__init__(self)
        gui.base.OutputBase.__init__(self, config)

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_IN)
        self.loaded = False

        self.view = OutputView(gui.theme.conv_theme, handler)
        self.view.connect('search_request', self._search_request_cb)
        self.clear()
        self.view.show()
        self.add(self.view)

    def _search_request_cb(self, view, link):
        self.emit("search_request", link)

    def clear(self, source="", target="", target_display="",
            source_img="", target_img=""):
        '''clear the content'''
        self.view.clear(source, target, target_display, source_img, target_img)
        self.pending = []

    def add_message(self, msg, scroll):
        if msg.type == "status":
            msg.message = Plus.msnplus_strip(msg.message)
        self.view.add_message(msg, self.config.b_allow_auto_scroll)

    def update_p2p(self, account, _type, *what):
        ''' new p2p data has been received (custom emoticons) '''
        if _type == 'emoticon':
            _creator, _friendly, path = what
            _id = base64.b64encode(_creator+xml.sax.saxutils.unescape(_friendly)) #see gui/base/MarkupParser.py
            mystr = "var now=new Date();var x=document.images;for(var i=0;i<x.length;i++){if(x[i].name=='%s'){x[i].src='%s?'+now.getTime();}}" % (_id, path)
            self.view.execute_script(mystr)
