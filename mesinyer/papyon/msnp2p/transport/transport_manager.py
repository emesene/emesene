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

from papyon.msnp2p.transport.switchboard import *
from papyon.msnp2p.transport.TLP import MessageBlob

import gobject
import struct
import logging

__all__ = ['P2PTransportManager']

logger = logging.getLogger('papyon.msnp2p.transport')


class P2PTransportManager(gobject.GObject):
    __gsignals__ = {
            "blob-received" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "blob-sent" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "chunk-transferred" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
    }

    def __init__(self, client):
        gobject.GObject.__init__(self)

        self._client = client
        switchboard_manager = self._client._switchboard_manager
        switchboard_manager.register_handler(SwitchboardP2PTransport, self)
        self._default_transport = \
                lambda transport_mgr, peer : \
                        SwitchboardP2PTransport(client, (peer,), transport_mgr)
        self._transports = set()
        self._transport_signals = {}
        self._signaling_blobs = {} # blob_id => blob
        self._data_blobs = {} # session_id => blob

    def _register_transport(self, transport):
        assert transport not in self._transports, "Trying to register transport twice"
        self._transports.add(transport)
        signals = []
        signals.append(transport.connect("chunk-received", self._on_chunk_received))
        signals.append(transport.connect("chunk-sent", self._on_chunk_sent))
        self._transport_signals[transport] = signals

    def _unregister_transport(self, transport):
        self._transports.discard(transport)
        signals = self._transport_signals[transport]
        for signal in signals:
            transport.disconnect(signal)
        del self._transport_signals[transport]

    def _get_transport(self, peer):
        for transport in self._transports:
            if transport.peer == peer:
                return transport
        return self._default_transport(self, peer)

    def _on_chunk_received(self, transport, chunk):
        self.emit("chunk-transferred", chunk)
        session_id = chunk.header.session_id
        blob_id = chunk.header.blob_id

        if session_id == 0: # signaling blob
            if blob_id in self._signaling_blobs:
                blob = self._signaling_blobs[blob_id]
            else:
                # create an in-memory blob
                blob = MessageBlob(chunk.application_id, "",
                    chunk.header.blob_size,
                    session_id, chunk.header.blob_id)
                self._signaling_blobs[blob_id] = blob
        else: # data blob
            if session_id in self._data_blobs:
                blob = self._data_blobs[session_id]
                if blob.transferred == 0:
                    blob.id = chunk.header.blob_id
            else:
                # create an in-memory blob
                blob = MessageBlob(chunk.application_id, "",
                        chunk.header.blob_size,
                        session_id, chunk.header.blob_id)
                self._data_blobs[session_id] = blob

        blob.append_chunk(chunk)
        if blob.is_complete():
            blob.data.seek(0, 0)
            self.emit("blob-received", blob)
            if session_id == 0:
                del self._signaling_blobs[blob_id]
            else:
                del self._data_blobs[session_id]

    def _on_chunk_sent(self, transport, chunk):
        self.emit("chunk-transferred", chunk)

    def _on_blob_sent(self, transport, blob):
        self.emit("blob-sent", blob)

    def send(self, peer, blob):
        transport = self._get_transport(peer)
        transport.send(blob, (self._on_blob_sent, transport, blob))

    def register_writable_blob(self, blob):
        if blob.session_id in self._data_blobs:
            logger.warning("registering already registered blob "\
                    "with session_id=" + str(session_id))
            return
        self._data_blobs[blob.session_id] = blob

gobject.type_register(P2PTransportManager)
