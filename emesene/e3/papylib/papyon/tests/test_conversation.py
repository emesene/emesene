# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2010 Collabora Ltd.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from base import *

sys.path.insert(0, "")

import os
import papyon

class ConversationClient(TestClient):

    def __init__(self):
        opts = [('-S', '--send',   {'type': 'string', 'default': '',
                                    'help': 'send message to invited contacts'}),
                ('-n', '--nudge',  {'action': 'store_true', 'default': False,
                                    'help': 'send nudge to invited contacts'}),
                ('-e', '--echo',   {'action': 'store_true', 'default': False,
                                    'help': 'echo received messages'}),
                ('-r', '--repeat', {'action': 'store_true', 'default': False,
                                    'help': 'repeat sent message every 2s'})
                ]
        args = [("participants", "list")]
        TestClient.__init__(self, "Conversation", opts, args,
                ConversationClientEvents)

    def connected(self):
        self.profile.presence = papyon.profile.Presence.ONLINE

        # parse and search participants for conversation
        contacts = []
        for account in self.arguments["participants"]:
            network = papyon.profile.NetworkID.MSN
            if ':' in account:
                account, network = account.split(":")
                network = int(network)
            contact = self.address_book.search_or_build_contact(account, network)
            contacts.append(contact)

        self._conversation = papyon.Conversation(self, contacts)
        self._conversation_handler = ConversationHandler(self, self._conversation)
        if self.options.send:
            gobject.timeout_add_seconds(2, self.send)
        if self.options.nudge:
            gobject.timeout_add_seconds(2, self.nudge)

    def send(self):
        message = papyon.ConversationMessage(self.options.send)
        self._conversation.send_text_message(message)
        return self.options.repeat

    def nudge(self):
        self._conversation.send_nudge()
        return self.options.repeat


class ConversationClientEvents(TestClientEvents):

    def __init__(self, client):
        TestClientEvents.__init__(self, client)

    def on_invite_conversation(self, conversation):
        print "*** Received invite for conversation"
        self._conversation_handler = ConversationHandler(self._client,
                conversation)


class ConversationHandler(papyon.event.ConversationEventInterface):

    def __init__(self, client, conversation):
        papyon.event.ConversationEventInterface.__init__(self, conversation)
        self._msn_client = client

    def on_conversation_state_changed(self, state):
        print "*** Conversation state changed to %s" % state

    def on_conversation_error(self, type, error):
        print "*** Conversation error: %s" % error

    def on_conversation_user_joined(self, contact):
        print "*** User %s joined conversation" % contact.account

    def on_conversation_user_left(self, contact):
        print "*** User %s left conversation" % contact.account

    def on_conversation_user_typing(self, contact):
        print "*** User %s is typing" % contact.account

    def on_conversation_message_received(self, sender, message):
        print "*** Received message from %s: %s" % (sender.account,
                message.content)
        if self._msn_client.options.echo:
            self._client.send_text_message(message)
    
    def on_conversation_nudge_received(self, sender):
        print "*** Received nudge from %s" % (sender.account)
        if self._msn_client.options.echo:
            self._client.send_nudge()

    def on_conversation_message_sent(self, message):
        print "*** Message has been sent"

    def on_conversation_nudge_sent(self):
        print "*** Nudge has been sent"

    def on_conversation_closed(self):
        print "*** Conversation has been closed"


if __name__ == "__main__":
    client = ConversationClient()
    client.run()
