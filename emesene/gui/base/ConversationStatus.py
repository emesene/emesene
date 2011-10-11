'''a module that contains a class that represents a conversation status
'''
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

import gui
import MarkupParser

class ConversationStatus(object):

    def __init__(self, config):
        #first message of contact
        self.first = True
        self.config = config
        self.last_incoming = None
        self.last_incoming_nickname = None
        self.last_incoming_account = None

    def pre_process_message(self, contact, message, incomming, cedict, cepath, tstamp=None, mtype=None, cstyle=None):
        '''Create a new gui.Message
        '''
        msg = gui.Message.from_contact(contact,
                message, self.first, incomming, tstamp, mtype = mtype, mstyle=cstyle)

        if self.config.b_show_emoticons:
            msg.message = MarkupParser.replace_emotes(MarkupParser.escape(msg.message),
                        cedict, cepath, msg.sender)

        msg.message = MarkupParser.urlify(msg.message)

        b_nick_check = bool(self.last_incoming_nickname != msg.display_name)
        if b_nick_check:
            self.last_incoming_nickname = msg.display_name

        if msg.incoming:
            if self.last_incoming is None:
                self.last_incoming = False

            msg.first = not self.last_incoming

            if self.last_incoming_account != msg.sender or b_nick_check:
                msg.first = True
        else:
            if self.last_incoming is None:
                self.last_incoming = True

            msg.first = self.last_incoming

        return msg

    def post_process_message(self, msg):

        if msg.incoming:
            self.last_incoming = True
            self.last_incoming_account = msg.sender
        else:
            self.last_incoming = False

        if msg.type == "status":
            self.last_incoming = None

    def update_status(self):
        self.first = False

    def clear(self):
        self.last_incoming = None
