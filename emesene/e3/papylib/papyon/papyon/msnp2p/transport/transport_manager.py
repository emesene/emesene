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

from papyon.msnp2p.SLP import *
from papyon.msnp2p.transport.switchboard import *
from papyon.msnp2p.transport.notification import *
from papyon.msnp2p.transport.TLP import MessageBlob

import gobject
import struct
import logging
import os

__all__ = ['P2PTransportManager']

logger = logging.getLogger('papyon.msnp2p.transport')


class P2PTransportManager(gobject.GObject):
    __gsignals__ = {
            "data-received" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                # peer, peer_guid, session_id, data
                (object, object, object, object)),

            "data-sent" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                # peer, peer_guid, session_id, data
                (object, object, object, object)),

            "data-transferred" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                # peer, peer_guid, session_id, size
                (object, object, object, object)),

            "slp-message-received" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                # peer, peer_guid, slp_message
                (object, object, object)),
    }

    def __init__(self, client):
        gobject.GObject.__init__(self)

        self._client = client
        switchboard_manager = self._client._switchboard_manager
        switchboard_manager.register_handler_class(SwitchboardP2PTransport, self)
        self._default_transport = lambda peer, peer_guid : \
            SwitchboardP2PTransport.handle_peer(client, peer, peer_guid, self)
        self._transports = set()
        self._transport_signals = {}
        self._data_blobs = {} # (peer, peer_guid, session_id) => blob
        self._blacklist = set() # blacklist of (peer, peer_guid, session_id)
        uun_transport = NotificationP2PTransport(client, self)

    # Public API -------------------------------------------------------------

    def send_slp_message(self, peer, peer_guid, application_id, message):
        self.send_data(peer, peer_guid, application_id, 0, str(message))

    def send_data(self, peer, peer_guid, application_id, session_id, data):
        blob = MessageBlob(application_id, data, None, session_id, None)
        transport = self._get_transport(peer, peer_guid, blob)
        transport.send(peer, peer_guid, blob)

    def register_data_buffer(self, peer, peer_guid, session_id, buffer, size):
        if (peer, peer_guid, session_id) in self._data_blobs:
            logger.warning("registering already registered blob "\
                    "with session_id=" + str(session_id))
            return
        blob = MessageBlob(0, buffer, size, session_id)
        self._data_blobs[(peer, peer_guid, session_id)] = blob

    def close(self):
        for transport in self._transports.copy():
            transport.close()

    def cleanup(self, peer, peer_guid, session_id):
        logger.info("Cleaning up session %s" % session_id)
        if (peer, peer_guid, session_id) in self._data_blobs:
            del self._data_blobs[(peer, peer_guid, session_id)]
        for transport in self._transports:
            if transport.peer == peer and transport.peer_guid == peer_guid:
                transport.cleanup(session_id)

    def add_to_blacklist(self, peer, peer_guid, session_id):
        """ Ignore data chunks received for this session_id: we want to
            ignore chunks received shortly after closing a session. """
        self._blacklist.add((peer, peer_guid, session_id))

    def remove_from_blacklist(self, peer, peer_guid, session_id):
        self._blacklist.discard((peer, peer_guid, session_id))

    # Transport registration -------------------------------------------------

    def _register_transport(self, transport):
        logger.info("Registering transport %s" % repr(transport))
        assert transport not in self._transports, "Trying to register transport twice"
        self._transports.add(transport)
        signals = []
        signals.append(transport.connect("chunk-received",
            self._on_chunk_received))
        signals.append(transport.connect("chunk-sent",
            self._on_chunk_sent))
        signals.append(transport.connect("blob-received",
            self._on_blob_received))
        signals.append(transport.connect("blob-sent",
            self._on_blob_sent))
        self._transport_signals[transport] = signals

    def _unregister_transport(self, transport):
        if transport not in self._transports:
            return
        logger.info("Unregistering transport %s" % repr(transport))
        self._transports.discard(transport)
        signals = self._transport_signals.pop(transport, [])
        for signal in signals:
            transport.disconnect(signal)

    # Transport selection ----------------------------------------------------

    def _get_transport(self, peer, peer_guid, blob):
        for transport in self._transports:
            if transport.can_send(peer, peer_guid, blob):
                return transport
        return self._default_transport(peer, peer_guid)

    # Chunk/blob demuxing ----------------------------------------------------

    def _on_chunk_received(self, transport, peer, peer_guid, chunk):
        session_id = chunk.session_id
        blob_id = chunk.blob_id
        key = (peer, peer_guid, session_id)

        if key in self._blacklist:
            return
        if chunk.size == 0 or (chunk.version == 1 and chunk.blob_size == 0):
            return

        if key in self._data_blobs:
            blob = self._data_blobs[key]
            if blob.transferred == 0:
                blob.id = chunk.blob_id
        else:
            # create an in-memory blob
            blob = MessageBlob(chunk.application_id, "",
                    chunk.blob_size, session_id, chunk.blob_id)
            self._data_blobs[key] = blob

        try:
            blob.append_chunk(chunk)
        except Exception, err:
            logger.exception(err)
            logger.warning("Couldn't append chunk to blob, ignoring it")
            return

        self._on_chunk_transferred(peer, peer_guid, chunk)
        if blob.is_complete():
            del self._data_blobs[key]
            self._on_blob_received(transport, peer, peer_guid, blob)

    def _on_chunk_sent(self, transport, peer, peer_guid, chunk):
        self._on_chunk_transferred(peer, peer_guid, chunk)

    def _on_chunk_transferred(self, peer, peer_guid, chunk):
        session_id = chunk.session_id
        size = chunk.size
        if chunk.has_progressed():
            self.emit("data-transferred", peer, peer_guid, session_id, size)

    def _on_blob_received(self, transport, peer, peer_guid, blob):
        # Determine if it's a signaling message or a data blob
        session_id = blob.session_id
        if session_id == 0:
            msg = self._parse_signaling_blob(blob)
            if msg and not self._handle_signaling_message(peer, peer_guid, msg):
                self.emit("slp-message-received", peer, peer_guid, msg)
        else:
            self.emit("data-received", peer, peer_guid, session_id, blob.data)

    def _on_blob_sent(self, transport, peer, peer_guid, blob):
        session_id = blob.session_id
        if session_id != 0:
            self.emit("data-sent", peer, peer_guid, session_id, blob.data)

    # Signaling messages handling --------------------------------------------

    def _handle_signaling_message(self, peer, peer_guid, message):
        """ Handle the SLP message if it's transport related.
            Returns True if the message has been handled. """
        if isinstance(message, SLPRequestMessage) and \
                isinstance(message.body, SLPTransportRequestBody):
            self._on_transport_request_received(peer, peer_guid, message)
            return True
        if isinstance(message, SLPResponseMessage) and \
                isinstance(message.body, SLPTransportResponseBody):
            self._on_transport_response_received(peer, peer_guid, message)
            return True
        return False

    def _on_transport_request_received(self, peer, peer_guid, message):
        logger.info("Received transport request from %s;{%s}" %
                (peer.account, peer_guid))
        return

    def _on_transport_response_received(self, peer, peer_guid, message):
        logger.info("Received transport response %i from %s;{%s}" %
                (message.status, peer.account, peer_guid))
        return

    # Utilities --------------------------------------------------------------

    def _parse_signaling_blob(self, blob):
        try:
            message = SLPMessage.build(blob.read_data())
        except Exception, err:
            logger.exception(err)
            logger.error('Received invalid SLP message')
            return None
        return message

gobject.type_register(P2PTransportManager)
