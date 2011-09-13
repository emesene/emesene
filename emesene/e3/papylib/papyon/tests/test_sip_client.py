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
from papyon.media.conference import *
from papyon.media.constants import *

class SIPClient(TestClient):

    def __init__(self):
        opts = [('-a', '--answer', {'type': 'choice', 'default': 'ignore',
                                    'choices': ('ignore', 'accept', 'reject'),
                                    'help': 'what to do on incoming call'}),
                ('-i', '--invite', {'type': 'string', 'default': '',
                                    'help': 'peer to send call invite to'})
                ]
        args = []
        TestClient.__init__(self, "SIP Call", opts, args, SIPClientEvents)

    def connected(self):
        self.profile.presence = papyon.profile.Presence.ONLINE
        self.profile.client_capabilities.has_webcam = True
        self.profile.client_capabilities.supports_rtc_video = True

        if self.options.invite:
            gobject.timeout_add_seconds(2, self.invite)

    def invite(self):
        contact = self.address_book.search_contact(self.options.invite,
                papyon.profile.NetworkID.MSN)

        if contact is None:
            print 'Unknown contact: %s' % self.options.invite
            return False

        call = self.call_manager.create_call(contact)
        self.call_handler = CallEvents(call)
        self.session_handler = MediaSessionHandler(call.media_session)
        stream = call.media_session.create_stream("audio",
                MediaStreamDirection.BOTH, True)
        call.media_session.add_stream(stream)
        stream = call.media_session.create_stream("video",
                MediaStreamDirection.BOTH, True)
        call.media_session.add_stream(stream)
        call.invite()

        return False


class SIPClientEvents(TestClientEvents):

    def __init__(self, client):
        TestClientEvents.__init__(self, client)

    def on_invite_conference(self, call):
        print "INVITED : call-id = %s" % call.id
        self.call_handler = CallEvents(call)
        self.session_handler = MediaSessionHandler(call.media_session)
        call.ring()
        if self._client.options.answer == 'accept':
            call.accept()
        elif self._client.options.answer == 'reject':
            call.reject()


class CallEvents(papyon.event.CallEventInterface):

    def __init__(self, call):
        papyon.event.CallEventInterface.__init__(self, call)


if __name__ == "__main__":
    client = SIPClient()
    client.run()
