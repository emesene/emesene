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

from papyon.msnp2p.transport.TLP import TLPFlag, MessageChunk, ControlBlob

import gobject
import logging
import weakref

__all__ = ['BaseP2PTransport']

logger = logging.getLogger('papyon.msnp2p.transport')

class BaseP2PTransport(gobject.GObject):
    __gsignals__ = {
            "chunk-received": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "chunk-sent": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            }

    def __init__(self, transport_manager, name):
        gobject.GObject.__init__(self)
        self._transport_manager = weakref.proxy(transport_manager)
        self._client = transport_manager._client
        self._name = name

        self._transport_manager._register_transport(self)
        self._reset()

    @property
    def name(self):
        return self._name

    @property
    def peer(self):
        raise NotImplementedError

    @property
    def rating(self):
        raise NotImplementedError

    @property
    def max_chunk_size(self):
        raise NotImplementedError

    def send(self, blob, callback=None, errback=None):
        if blob.is_control_blob():
            self._control_blob_queue.append((blob, callback, errback))
        else:
            self._data_blob_queue.append((blob, callback, errback))
        gobject.timeout_add(200, self._process_send_queues)
        self._process_send_queues()

    def close(self):
        self._transport_manager._unregister_transport(self)

    def _send_chunk(self, chunk):
        raise NotImplementedError

    # Helper methods
    def _reset(self):
        self._control_blob_queue = []
        self._data_blob_queue = []
        self._pending_blob = {} # blob_id : (blob, callback, errback)
        self._pending_ack = {} # blob_id : [blob_offset1, blob_offset2 ...]

    def _add_pending_ack(self, blob_id, chunk_id=0):
        if blob_id not in self._pending_ack:
            self._pending_ack[blob_id] = set()
        self._pending_ack[blob_id].add(chunk_id)

    def _del_pending_ack(self, blob_id, chunk_id=0):
        if blob_id not in self._pending_ack:
            return
        self._pending_ack[blob_id].discard(chunk_id)

        if len(self._pending_ack[blob_id]) == 0:
            del self._pending_ack[blob_id]

    def _on_chunk_received(self, chunk):
        if chunk.require_ack():
            self._send_ack(chunk)

        if chunk.header.flags & TLPFlag.ACK:
            self._del_pending_ack(chunk.header.dw1, chunk.header.dw2)
            if chunk.header.dw1 in self._pending_blob:
                blob, callback, errback = self._pending_blob[chunk.header.dw1]
                del self._pending_blob[blob.id]
                if callback:
                    callback[0](*callback[1:])

        #FIXME: handle all the other flags

        if not chunk.is_control_chunk():
            self.emit("chunk-received", chunk)

        self._process_send_queues()

    def _on_chunk_sent(self, chunk):
        self.emit("chunk-sent", chunk)
        self._process_send_queues()

    def _process_send_queues(self):
        if len(self._control_blob_queue) > 0:
            queue = self._control_blob_queue
        elif len(self._data_blob_queue) > 0:
            queue = self._data_blob_queue
        else:
            return False

        blob, callback, errback = queue[0]
        chunk = blob.get_chunk(self.max_chunk_size)
        if blob.is_complete():
            queue.pop(0)
            if blob.is_data_blob():
                self._pending_blob[blob.id] = (blob, callback, errback)
            elif callback:
                callback[0](*callback[1:])

        if chunk.require_ack() :
            self._add_pending_ack(chunk.header.blob_id, chunk.header.dw1)
        self._send_chunk(chunk)
        return True

    def _send_ack(self, received_chunk):
        flags = received_chunk.header.flags

        flags = TLPFlag.ACK
        if received_chunk.header.flags & TLPFlag.RAK:
            flags |= TLPFlag.RAK

        ack_blob = ControlBlob(received_chunk.header.session_id, flags,
                dw1 = received_chunk.header.blob_id,
                dw2 = received_chunk.header.dw1,
                qw1 = received_chunk.header.blob_size)

        self.send(ack_blob)

gobject.type_register(BaseP2PTransport)
