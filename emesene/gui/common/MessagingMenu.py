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
import gui.gtkui.utils as utils
import indicate

import gui

class MessagingMenu(gui.BaseTray):
    """
    A widget that implements the messaging menu for ubuntu
    """
    NAME = 'Messaging Menu'
    DESCRIPTION = 'The Ayatana Messaging Menu extension'
    AUTHOR = 'Cando, Tom Cowell'
    WEBSITE = 'www.emesene.org'

    def __init__ (self, handler, main_window=None):
        '''constructor'''
        gui.BaseTray.__init__(self, handler)
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

    def set_visible(self, arg):
        """ we are exiting from emesene: disconnect all signals """
        if arg:
            return

        for key in self.r_indicator_dict.keys():
            ind = self.r_indicator_dict[key]
            if ind is not None:
                ind.hide()
            if self.indicator_dict[ind] is not None:
                del self.indicator_dict[ind]
            if self.r_indicator_dict[key] is not None:
                del self.r_indicator_dict[key]

        gui.BaseTray.set_visible(self, True)

        self.server.disconnect(self.sid)
        self.server.hide()
        self.server = None
        self.sid = None

    def _on_conv_message(self, cid, account, msgobj, cedict=None):
        """
        This is fired when a new message arrives to a user.
        """
        contact = self.handler.session.contacts.get(account)
        conv_manager = self.handler.session.get_conversation_manager(cid, [account])
        conv = conv_manager.has_similar_conversation(cid, [account])
        if conv is None:
            return # it can happen, just quickly open/close a conv
        icid = conv.icid

        if icid not in self.indicator_dict.values() and conv_manager and \
            not (conv_manager.is_active() and conv.members == [account]):

            self._create_indicator("im", gui.Plus.msnplus_strip(
                contact.nick), account, icid=icid)

    def _on_message_read(self, conv):
        """
        This is called when the user read the message.
        """
        if conv and conv.icid in self.r_indicator_dict.keys():
            ind = self.r_indicator_dict[conv.icid]

            if ind is not None:
                ind.hide()

                if self.indicator_dict[ind] is not None:
                    del self.indicator_dict[ind]

                if self.r_indicator_dict[conv.icid] is not None:
                    del self.r_indicator_dict[conv.icid]

    def _on_conv_ended(self, cid):
        """
        Called when the user close the conversation.
        """
        conv = self.handler.session.get_conversation(cid)
        if conv and conv.icid in self.r_indicator_dict.keys():
            ind = self.r_indicator_dict[conv.icid]
            ind.hide()
            del self.r_indicator_dict[conv.icid]

    def _create_indicator(self, subtype, sender, body,
                          extra_text = '', icid=None):
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
            pixbuf = utils.safe_gtk_pixbuf_load(contact.picture or '', (48, 48))
            if pixbuf is not None:
                ind.set_property_icon("icon", pixbuf)

            ind.set_property("subtype", subtype)
            ind.set_property("sender", sender + extra_text)
            if icid is not None:
                ind.set_property("body", str(icid))
            else:
                ind.set_property("body", body)
            ind.set_property_time("time", time.time())
            ind.set_property("draw-attention", "true")
            ind.connect("user-display", self._display)
            ind.show()

            # Add indicator to the dictionary
            if subtype == "im":
                self.indicator_dict[ind] = icid
                self.r_indicator_dict[icid] = ind

            for old_icid in self.indicator_dict.values():
                if old_icid not in self.handler.session.conversations.keys():
                    # workaround: kill the orphan indicator
                    ind = self.r_indicator_dict[old_icid]
                    del self.indicator_dict[ind]
                    del self.r_indicator_dict[old_icid]
        else:
            return

    def _display(self, indicator, arg=None):
        """
        This is fired when a user clicks on the indicator item in the applet.
        """
        subtype = indicator.get_property("subtype")

        if subtype == "im":
            icid = self.indicator_dict[indicator]

            convman = self.handler.session.get_conversation_manager(icid)

            if convman:
                conv = convman.has_similar_conversation(icid)
                convman.present(conv)

        if self.indicator_dict[indicator] is not None:
            del self.indicator_dict[indicator]
        if self.r_indicator_dict[icid] is not None:
            del self.r_indicator_dict[icid]

        # Hide the indicator - user has clicked it so we've no use for it now.
        indicator.hide()


    def _server_display(self, server, arg=None):
        """
        This is fired when the user clicks on the server indicator item.
        """
        self.main_window.present()
