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

import logging
log = logging.getLogger("gui.common.NumerableTrayIcon")

import e3
import gui

class NumerableTrayIcon(gui.BaseTray):

    def __init__ (self, handler=None):
        '''constructor'''
        gui.BaseTray.__init__(self, handler)
        self.count = 0
        self.session = None
        self.last_new_message = None
        self.icid_dict = {}

    def _on_conv_message(self, cid, account, msgobj, cedict=None):
        """
        This is fired when a new message arrives to a user.
        """
        conv_manager = self.handler.session.get_conversation_manager(cid, [account])
        if not conv_manager:
            return

        conv = conv_manager.has_similar_conversation(cid, [account])
        icid = conv.icid
        if icid in self.icid_dict.keys():
            self.icid_dict[icid] += 1
        elif conv_manager.is_active():
            return
        else:
            self.icid_dict[icid] = 1

        self.count += 1
        self.last_new_message = cid

    def _on_message_read(self, conv):
        """
        This is called when the user read the message.
        """
        self.last_new_message = None
        if conv:
            self._hide_count(conv.icid)

    def _on_conv_ended(self, cid):
        """
        This is called when the conversation ends
        """
        conv = self.handler.session.get_conversation(cid)
        if conv:
            self._hide_count(conv.icid)

    def _hide_count(self, icid):
        ''' Hide the message count if nessecary '''
        if icid in self.icid_dict.keys():
            self.count -= self.icid_dict[icid]
            del self.icid_dict[icid]
        if self.icid_dict == {}:
            self.count = 0
        self.count_changed(self.count)

    def count_changed(self, count):
        '''method called when unread message count changes'''
        pass
