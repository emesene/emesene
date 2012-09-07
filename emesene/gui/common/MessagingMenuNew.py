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

import time
from gi.repository import MessagingMenu, Gio

import gui
import e3

class MessagingMenuNew(gui.BaseTray):
    """
    A widget that implements the messaging menu for ubuntu
    """
    NAME = 'Messaging Menu'
    DESCRIPTION = 'The Messaging Menu extension'
    AUTHOR = 'Sven (Sbte)'
    WEBSITE = 'www.emesene.org'

    def __init__ (self, handler, main_window=None):
        '''constructor'''
        gui.BaseTray.__init__(self, handler)
        self.main_window = main_window
        self.source_list = []

        self.mmapp = MessagingMenu.App(desktop_id="emesene.desktop")
        self.mmapp.register()
        self.mmapp.connect('activate-source', self._on_source_activated)
        self.mmapp.connect('status-changed', self._on_set_status)

    def unsubscribe(self):
        self.disconnect_signals()
        for icid in self.source_list:
            self._remove_source(icid=icid)

    def hide(self):
        self.unsubscribe()
        self.mmapp.unregister()

    def _on_conv_message(self, cid, account, msgobj, cedict=None):
        """
        This is fired when a new message arrives to a user.
        """
        contact = self.handler.session.contacts.safe_get(account)

        conv_manager = self.handler.session.get_conversation_manager(cid, [account])
        conv = conv_manager.has_similar_conversation(cid, [account])
        if conv is None:
            return
        icid = conv.icid

        if icid not in self.source_list and not conv_manager.is_active():
            self._add_source(account, icid)

    def _on_message_read(self, conv):
        """
        This is called when the user read the message.
        """
        self._remove_source(conv=conv)

    def _on_conv_ended(self, icid):
        """
        Called when the user close the conversation.
        """
        self._remove_source(icid=icid)

    def _on_status_change_succeed(self, status):
        """
        change the icon in the tray according to user's state
        """
        if status == e3.status.ONLINE:
            self.mmapp.set_status(MessagingMenu.Status.AVAILABLE)
        elif status == e3.status.AWAY:
            self.mmapp.set_status(MessagingMenu.Status.AWAY)
        elif status == e3.status.IDLE:
            self.mmapp.set_status(MessagingMenu.Status.AWAY)
        elif status == e3.status.BUSY:
            self.mmapp.set_status(MessagingMenu.Status.BUSY)
        elif status == e3.status.OFFLINE:
            self.mmapp.set_status(MessagingMenu.Status.INVISIBLE)

    def _remove_source(self, conv=None, icid=None):
        cid = -1
        if icid and icid in self.source_list:
            cid = icid
        elif conv and conv.icid in self.source_list:
            cid = conv.icid

        if self.mmapp.has_source(str(cid)):
            self.mmapp.remove_source(str(cid))
            self.source_list.remove(cid)

    def _add_source(self, account, icid):
        contact = self.handler.session.contacts.safe_get(account)
        nick = gui.Plus.msnplus_strip(contact.nick)
        icon_file = Gio.file_parse_name(contact.picture or gui.theme.image_theme.user)
        icon = Gio.FileIcon.new(icon_file)
        self.mmapp.append_source(str(icid), icon, nick)
        self.mmapp.draw_attention(str(icid))
        self.source_list.append(icid)

    def _on_source_activated(self, mmapp, source):
        icid = float(source)
        conv_manager = self.handler.session.get_conversation_manager(icid)
        if conv_manager is None:
            return

        self.conv_manager.present()

    def _on_set_status(self, mmapp, status):
        if not self.handler.session:
            return

        if status == MessagingMenu.Status.OFFLINE:
            self.handler.session.close()
        elif status == MessagingMenu.Status.AVAILABLE:
            self.handler.session.set_status(e3.status.ONLINE)
        elif status == MessagingMenu.Status.AWAY:
            self.handler.session.set_status(e3.status.AWAY)
        elif status == MessagingMenu.Status.BUSY:
            self.handler.session.set_status(e3.status.BUSY)
        elif status == MessagingMenu.Status.INVISIBLE:
            self.handler.session.set_status(e3.status.OFFLINE)
