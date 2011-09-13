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

class FileTransferClient(TestClient):

    def __init__(self):
        opts = [('-a', '--answer', {'type': 'choice', 'default': 'ignore',
                                    'choices': ('ignore', 'accept', 'reject'),
                                    'help': 'what to do on incoming file'}),
                ('-w', '--write',   {'type': 'string', 'default': '',
                                    'help': 'path to write received file'}),
                ('-S', '--send',   {'type': 'string', 'nargs': 2,
                                    'help': 'send file [recipient path]'})
                ]
        args = []
        TestClient.__init__(self, "File Transfer", opts, args,
                FileTransferClientEvents)

    def connected(self):
        self.profile.presence = papyon.profile.Presence.ONLINE
        if self.options.send:
            gobject.timeout_add_seconds(2, self.send)

    def send(self):
        recipient, path = self.options.send

        # get recipient
        contact = self.address_book.search_or_build_contact(recipient,
                papyon.profile.NetworkID.MSN)

        # get file details
        filename = os.path.basename(path)
        data = file(path, 'r')
        data.seek(0, os.SEEK_END)
        size = data.tell()
        data.seek(0, os.SEEK_SET)

        self._session = self.ft_manager.send(contact, filename, size, data)
        self._session_handler = FileTransferHandler(self._session)

    def accept(self, session):
        self._session = session
        self._session_handler = FileTransferHandler(session)
        buffer = None
        if self.options.write:
            buffer = file(self.options.write, 'w')
        session.accept(buffer)

class FileTransferClientEvents(TestClientEvents):

    def __init__(self, client):
        TestClientEvents.__init__(self, client)

    def on_invite_file_transfer(self, session):
        print "** Invite for \"%s\" (%i bytes)" % (session.filename, session.size)
        if self._client.options.answer == 'accept':
            gobject.timeout_add_seconds(2, self._client.accept, session)
        elif self._client.options.answer == 'reject':
            session.reject()


class FileTransferHandler(papyon.event.P2PSessionEventInterface):

    def __init__(self, session):
        papyon.event.P2PSessionEventInterface.__init__(self, session)
        self._transferred = 0

    def on_session_accepted(self):
        print "** Session has been accepted"

    def on_session_rejected(self):
        print "** Session has been rejected"

    def on_session_completed(self, data):
        print "** Session has been completed"

    def on_session_canceled(self):
        print "** Session has been canceled"

    def on_session_disposed(self):
        print "** Session has been disposed"

    def on_session_progressed(self, size):
        self._transferred += size
        print "** Received %i / %i" % (self._transferred, self._client.size)


if __name__ == "__main__":
    client = FileTransferClient()
    client.run()
