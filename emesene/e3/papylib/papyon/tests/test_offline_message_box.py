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

import papyon

class OIMClient(TestClient):

    def __init__(self):
        opts = [('-f', '--fetch',  {'action': 'store_true', 'default': False,
                                    'help': 'fetch message when receiving'}),
                ('-d', '--delete', {'action': 'store_true', 'default': False,
                                    'help': 'delete message after fetching'}),
                ('-S', '--send',   {'type': 'string', 'nargs': 2,
                                    'help': 'send message [recipient message]'})
                ]
        args = []
        TestClient.__init__(self, "OIM", opts, args, OIMClientEvents)

    def connected(self):
        self.profile.presence = papyon.profile.Presence.ONLINE

        if self.options.send:
            gobject.timeout_add_seconds(2, self.send)

    def send(self):
        recipient, message = self.options.send

        contact = self.address_book.search_or_build_contact(recipient,
                papyon.profile.NetworkID.MSN)
        self.oim_box.send_message(contact, message)


class OIMClientEvents(TestClientEvents,
                      papyon.event.OfflineMessagesEventInterface):

    def __init__(self, client):
        TestClientEvents.__init__(self, client)
        papyon.event.OfflineMessagesEventInterface.__init__(self, client)

    def on_oim_messages_received(self, messages):
        for message in messages:
            if message.sender is None:
                continue
            print 'Received offline message from %s (%s)' % \
                (message.display_name, message.sender.account)

        if self._client.options.fetch:
            self._client.oim_box.fetch_messages(messages)

    def on_oim_messages_fetched(self, messages):
        for message in messages:
            if message.sender is None:
                continue
            print 'Fetched offline message from %s (%s)' % \
                (message.display_name, message.sender.account)
            print message.text

        if self._client.options.delete:
            self._client.oim_box.delete_messages(messages)

    def on_oim_messages_deleted(self, messages):
        for message in messages:
            if message.sender is None:
                continue
            print 'Deleted offline message from %s (%s)' % \
                (message.display_name, message.sender.account)


if __name__ == "__main__":
    client = OIMClient()
    client.run()

