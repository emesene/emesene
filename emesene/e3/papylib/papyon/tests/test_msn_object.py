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
import papyon.util.string_io as StringIO

class MSNObjectClient(TestClient):

    def __init__(self):
        opts = [('-a', '--auto',    {'action': 'store_true', 'default': False,
                                     'help': 'auto-request new display pictures'}),
                ('-c', '--change',  {'type': 'string', 'default': '',
                                    'help': 'path for new display picture'}),
                ('-r', '--request', {'type': 'string', 'default': '',
                                    'help': 'request display picture'}),
                ('-w', '--write',   {'type': 'string', 'default': '',
                                    'help': 'path to write received object'})
                ]
        args = []
        TestClient.__init__(self, "MSN Object", opts, args,
                MSNObjectClientEvents)

    def connected(self):
        self.profile.presence = papyon.profile.Presence.ONLINE
        self.profile.display_name = "Collabora1"
        if self.options.change:
            self.change()
        if self.options.request:
            gobject.timeout_add_seconds(2, self.request)

    def change(self):
        filename = os.path.basename(self.options.change)
        self._data = file(self.options.change, 'r').read()
        msn_object = papyon.p2p.MSNObject(self.profile, len(self._data),
                         papyon.p2p.MSNObjectType.DISPLAY_PICTURE,
                         filename, "", data=StringIO.StringIO(self._data))
        self.profile.msn_object = msn_object

    def request(self):
        recipient = self.options.request
        contact = self.address_book.search_or_build_contact(recipient,
                papyon.profile.NetworkID.MSN)
        self.msn_object_store.request(contact.msn_object, (self.retrieved,),
                peer=contact)

    def retrieved(self, msn_object):
        print "*** MSN Object has been retrieved"
        if self.options.write:
            f = file(self.options.write, 'w')
            f.write(msn_object._data)
            f.close()


class MSNObjectClientEvents(TestClientEvents):

    def __init__(self, client):
        TestClientEvents.__init__(self, client)

    def on_profile_msn_object_changed(self):
        self.on_contact_msn_object_changed(self._client.profile)

    def on_contact_msn_object_changed(self, contact):
        if self._client.options.auto:
            self._client.msn_object_store.request(contact.msn_object, None,
                peer=contact)


if __name__ == "__main__":
    client = MSNObjectClient()
    client.run()
