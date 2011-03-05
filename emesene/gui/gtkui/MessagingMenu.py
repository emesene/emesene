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
import time
import utils
import indicate

from BaseTray import BaseTray

class MessagingMenu(BaseTray):
    """
    A widget that implements the messaging menu for ubuntu
    """
    NAME = 'Messaging Menu'
    DESCRIPTION = 'The Ayatana Messaging Menu extension'
    AUTHOR = 'Cando, Tom Cowell'
    WEBSITE = 'www.emesene.org'

    def __init__ (self, handler, main_window=None):
        '''constructor'''
        BaseTray.__init__(self)
        self.handler = handler
        self.main_window = main_window
        self.signals_have_been_connected = False
        # if system-wide desktop file is not present
        # fallback to a custom .desktop file to be placed in /mesinyer/
        self.desktop_file = os.path.join("/usr/share/applications/",
                                         "emesene.desktop")
        if not utils.file_readable(self.desktop_file):
            self.desktop_file = os.path.join(os.getcwd(),
                                    "data/share/applications/emesene.desktop")

        self.indicator_dict = {}
        self.r_indicator_dict = {}

        self.server = indicate.indicate_server_ref_default()
        self.server.set_type("message.emesene")
        self.server.set_desktop_file(self.desktop_file)
        self.sid = self.server.connect("server-display", self._server_display)
        self.server.show()

    def set_main(self, session):
        """
        method called to set the state to the main window
        """
        self.handler.session = session
        self.handler.session.signals.conv_message.subscribe(
            self._on_message)
        self.handler.session.signals.conv_ended.subscribe(
            self._on_conv_ended)
        self.handler.session.signals.message_read.subscribe(
            self._on_message_read)

        self.signals_have_been_connected = True

    def set_visible(self, arg):
        """ we are exiting from emesene: disconnect all signals """
        if arg:
	    #FIXME: Hack to workaround bug #330. hide all indicators
	    for key in self.indicator_dict.keys():
               key.hide()
            return

        for key in self.r_indicator_dict.keys():
            ind = self.r_indicator_dict[key]
            if ind is not None:
                ind.hide()
            if self.indicator_dict[ind] is not None:
                del self.indicator_dict[ind]
            if self.r_indicator_dict[key] is not None:
                del self.r_indicator_dict[key]

        if self.signals_have_been_connected:
            self.handler.session.signals.conv_message.unsubscribe(
                self._on_message)
            self.handler.session.signals.conv_ended.unsubscribe(
                self._on_conv_ended)
            self.handler.session.signals.message_read.unsubscribe(
                self._on_message_read)

        self.server.disconnect(self.sid)
        self.server.hide()
        self.server = None
        self.sid = None

    def _on_message(self, cid, account, msgobj, cedict=None):
        """
        This is fired when a new message arrives to a user.
        """
        contact = self.handler.session.contacts.get(account)
        if cid not in self.indicator_dict.values():

            conv_manager = self._get_conversation_manager(cid, account)

            if conv_manager:
                conv = conv_manager.conversations[cid]

                if not (conv_manager.is_active() and \
                         conv.members == [account]):

                    self._create_indicator("im", contact.nick, account, cid=cid)

    def _on_message_read(self, conv):
        """
        This is called when the user read the message.
        """
        if conv and conv.cid in self.r_indicator_dict.keys():
            ind = self.r_indicator_dict[conv.cid]

            if ind is not None:
                ind.hide()

                if self.indicator_dict[ind] is not None:
                    del self.indicator_dict[ind]

                if self.r_indicator_dict[conv.cid] is not None:
                    del self.r_indicator_dict[conv.cid]

    def _on_conv_ended(self, cid):
        """
        Called when the user close the conversation.
        """
        if cid in self.r_indicator_dict.keys():
            ind = self.r_indicator_dict[cid]
            ind.hide()
            del self.r_indicator_dict[cid]

    def _create_indicator(self, subtype, sender, body,
                          extra_text = '', cid=None):
        """
        This creates a new indicator item, called by on_message, online & offline.
        """
        if indicate:
            try:
                # Ubuntu 9.10+
                ind = indicate.Indicator()
            except Exception:
                # Ubuntu 9.04
                ind = indicate.IndicatorMessage()

            #Get user icon.
            contact = self.handler.session.contacts.get(body)
            pixbuf = utils.safe_gtk_pixbuf_load(contact.picture, (48, 48))
            if pixbuf is not None:
                ind.set_property_icon("icon", pixbuf)

            ind.set_property("subtype", subtype)
            ind.set_property("sender", sender + extra_text)
            if cid is not None:
                ind.set_property("body", str(cid))
            else:
                ind.set_property("body", body)
            ind.set_property_time("time", time.time())
            ind.set_property("draw-attention", "true")
            ind.connect("user-display", self._display)
            ind.show()

            # Add indicator to the dictionary
            if subtype == "im":
                self.indicator_dict[ind] = cid
                self.r_indicator_dict[cid] = ind

        else:
            return

    def _display(self, indicator, arg=None):
        """
        This is fired when a user clicks on the indicator item in the applet.
        """
        subtype = indicator.get_property("subtype")

        if subtype == "im":
            cid = self.indicator_dict[indicator]

            convman = self._get_conversation_manager(cid)

            if convman:
                conv = self._get_conversation(cid)
                convman.present(conv)

        if self.indicator_dict[indicator] is not None:
            del self.indicator_dict[indicator]
        if self.r_indicator_dict[conv.cid] is not None:
            del self.r_indicator_dict[conv.cid]

        # Hide the indicator - user has clicked it so we've no use for it now.
        indicator.hide()


    def _server_display(self, server, arg=None):
        """
        This is fired when the user clicks on the server indicator item.
        """
        self.main_window.present()

