# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2007 Ali Sabil <asabil@gmail.com>
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

from papyon.msnp.message import MessageAcknowledgement
from papyon.msnp2p.transport.TLP import MessageChunk
from papyon.msnp2p.transport.base import BaseP2PTransport
from papyon.switchboard_manager import SwitchboardClient

import gobject
import struct
import logging

__all__ = ['SwitchboardP2PTransport']

logger = logging.getLogger('papyon.msnp2p.transport')


class SwitchboardP2PTransport(BaseP2PTransport, SwitchboardClient):
    def __init__(self, client, contacts, transport_manager):
        SwitchboardClient.__init__(self, client, contacts)
        BaseP2PTransport.__init__(self, transport_manager, "switchboard")


    def close(self):
        BaseP2PTransport.close(self)
        self._leave()

    @staticmethod
    def _can_handle_message(message, switchboard_client=None):
        content_type = message.content_type[0]
        return content_type == 'application/x-msnmsgrp2p'

    @property
    def peer(self):
        for peer in self.total_participants:
            return peer
        return None

    @property
    def rating(self):
        return 0

    @property
    def max_chunk_size(self):
        return 1250 # length of the chunk including the header but not the footer

    def _send_chunk(self, chunk):
        headers = {'P2P-Dest': self.peer.account}
        content_type = 'application/x-msnmsgrp2p'
        body = str(chunk) + struct.pack('>L', chunk.application_id)
        self._send_message(content_type, body, headers,
                MessageAcknowledgement.MSNC, self._on_chunk_sent, (chunk,))

    def _on_message_received(self, message):
        chunk = MessageChunk.parse(message.body[:-4])
        chunk.application_id = struct.unpack('>L', message.body[-4:])[0]
        self._on_chunk_received(chunk)

    def _on_contact_joined(self, contact):
        pass

    def _on_contact_left(self, contact):
        self.close()

