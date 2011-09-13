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
from papyon.service.ContentRoaming import *

class ContentRoamingClient(TestClient):

    def __init__(self):
        opts = [("-a", "--action", {'type': 'choice', 'choices': ('get', 'put'),
                                    'help': 'action: get or put',
                                    'default': 'get'})]
        args = [("nickname", "string"),
                ("message", "string"),
                ("path", "string")]
        TestClient.__init__(self, "Content Roaming", opts, args, ContentRoamingClientEvents)

    def connected(self):
        self.content_roaming.sync()


class ContentRoamingClientEvents(TestClientEvents,
                                 papyon.event.ContentRoamingEventInterface):

    def __init__(self, client):
        TestClientEvents.__init__(self, client)
        papyon.event.ContentRoamingEventInterface.__init__(self, client)

    def on_content_roaming_state_changed(self, state):
        if state == ContentRoamingState.SYNCHRONIZED:
            path = self.arguments['path']
            if self.options.action == 'get':
                type, data = self._client.content_roaming.display_picture
                f = open(path, 'w')
                f.write(data)
            elif self.options.action == 'put':
                f = open(path, 'r')
                self._client.content_roaming.store(self.arguments['nickname'],
                    self.arguments['message'], f.read())


if __name__ == "__main__":
    client = ContentRoamingClient()
    client.run()
