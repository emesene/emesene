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

from papyon.msnp.constants import UserNotificationTypes
from papyon.msnp2p.transport.TLP import MessageBlob
from papyon.msnp2p.transport.base import BaseP2PTransport

import gobject
import struct
import logging

__all__ = ['NotificationP2PTransport']

logger = logging.getLogger('papyon.msnp2p.transport.notification')

class NotificationP2PTransport(BaseP2PTransport):
    def __init__(self, client, transport_manager):
        BaseP2PTransport.__init__(self, transport_manager, "notification")
        self._protocol = client._protocol
        self._protocol.connect("buddy-notification-received",
                self._on_notification_received)

    def close(self):
        BaseP2PTransport.close(self)

    @property
    def rating(self):
        return 0

    @property
    def max_chunk_size(self):
        return 7500

    @property
    def peer(self):
        return None

    @property
    def peer_guid(self):
        return None

    def can_send(self, peer, peer_guid, blob, bootstrap=False):
        if not bootstrap:
            return False # can only handle bootstrap signaling
        if blob.total_size > self.max_chunk_size:
            return False # can't split in chunks
        if not peer.client_capabilities.p2p_bootstrap_via_uun:
            return False # peer needs to support UUN bootstrap
        return True

    def send(self, peer, peer_guid, blob):
        data = blob.read_data()
        self._protocol.send_user_notification(data, peer, peer_guid,
                UserNotificationTypes.P2P_DATA,
                (self._on_notification_sent, peer, peer_guid, blob))

    def _on_notification_received(self, protocol, peer, peer_guid, type, data):
        if type is not UserNotificationTypes.P2P_DATA:
            return
        blob = MessageBlob(0, data, None, 0)
        self.emit("blob-received", peer, peer_guid, blob)

    def _on_notification_sent(self, peer, peer_guid, blob):
        self.emit("blob-sent", peer, peer_guid, blob)
