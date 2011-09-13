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

from papyon.msnp2p.transport.TLP import MessageBlob

import gobject
import logging
import random
import threading
import weakref

__all__ = ['BaseP2PTransport']

logger = logging.getLogger('papyon.msnp2p.transport')


MAX_INT32 = 2147483647

class BaseP2PTransport(gobject.GObject):
    __gsignals__ = {
            "chunk-received": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object, object, object)), # peer, peer_guid, chunk

            "chunk-sent": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object, object, object)), # peer, peer_guid, chunk

            "blob-received": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object, object, object)), # peer, peer_guid, blob

            "blob-sent": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object, object, object)), # peer, peer_guid, blob
            }

    def __init__(self, transport_manager, name):
        gobject.GObject.__init__(self)
        self._transport_manager = weakref.proxy(transport_manager)
        self._client = transport_manager._client
        self._name = name
        self._source = None

        self._local_chunk_id = None
        self._remote_chunk_id = None

        self._queue_lock = threading.Lock()
        self._reset()
        self._transport_manager._register_transport(self)

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

    @property
    def version(self):
        if self._client.profile.client_id.supports_p2pv2 and \
                self.peer.client_capabilities.supports_p2pv2:
            return 2
        else:
            return 1

    def can_send(self, peer, peer_guid, blob, bootstrap=False):
        raise NotImplementedError

    def has_data_to_send(self):
        return (len(self._data_blob_queue) > 0)

    def send(self, peer, peer_guid, blob):
        self._queue_lock.acquire()
        queue = self._data_blob_queue.setdefault(blob.session_id, [])
        queue.append((peer, peer_guid, blob))
        self._queue_lock.release()
        self._start_processing()

    def cleanup(self, session_id):
        # remove this session's blobs from the data queue
        self._queue_lock.acquire()
        if session_id in self._data_blob_queue:
            del self._data_blob_queue[session_id]
        self._queue_lock.release()

    def close(self):
        self._stop_processing()
        self._reset()
        self._transport_manager._unregister_transport(self)

    def _ready_to_send(self):
        raise NotImplementedError

    def _send_chunk(self, peer, peer_guid, chunk):
        raise NotImplementedError

    # Helper methods ---------------------------------------------------------

    def _reset(self):
        self._queue_lock.acquire()
        self._first = True
        self._data_blob_queue = {} # session_id : [(peer, peer_guid, blob)]
        self._outgoing_chunks = {} # chunk : blob
        self._pending_ack = set()
        self._queue_lock.release()

    def _add_pending_ack(self, ack_id):
        self._pending_ack.add(ack_id)

    def _del_pending_ack(self, ack_id):
        self._pending_ack.discard(ack_id)

    def _on_chunk_received(self, peer, peer_guid, chunk):
        if chunk.is_data_preparation_chunk():
            return

        if self._first and not chunk.is_syn_request():
            self._first = False

        if chunk.require_ack():
            ack_chunk = chunk.create_ack_chunk(self._first)
            self._first = False
            self.__send_chunk(peer, peer_guid, ack_chunk)

        if chunk.is_ack_chunk() or chunk.is_nak_chunk():
            self._del_pending_ack(chunk.acked_id)

        #FIXME: handle all the other flags (NAK...)

        if not chunk.is_control_chunk():
            self.emit("chunk-received", peer, peer_guid, chunk)

        self._start_processing()

    def _on_chunk_sent(self, peer, peer_guid, chunk):
        if not chunk.is_data_preparation_chunk():
            self.emit("chunk-sent", peer, peer_guid, chunk)

        blob = self._outgoing_chunks.pop(chunk, None)
        if blob and blob.is_complete() and blob not in self._outgoing_chunks.values():
            if not chunk.is_data_preparation_chunk():
                self.emit("blob-sent", peer, peer_guid, blob)
        self._start_processing()

    def _start_processing(self):
        if self._source is None:
            self._source = gobject.timeout_add(200, self._process_send_queue)
        self._process_send_queue()

    def _stop_processing(self):
        if self._source is not None:
            gobject.source_remove(self._source)
            self._source = None

    def _process_send_queue(self):
        if not self._queue_lock.acquire(False):
            return True
        if not self.has_data_to_send():
            self._queue_lock.release()
            return False

        # FIXME find a better algorithm to choose session
        if 0 in self._data_blob_queue:
            session_id = 0
        else:
            session_id = self._data_blob_queue.keys()[0]

        if session_id != 0 and not self._ready_to_send():
            logger.info("Transport is not ready to send, bail out")
            self._queue_lock.release()
            return False

        sync = self._first
        self._first = False
        (peer, peer_guid, blob) = self._data_blob_queue[session_id][0]

        try:
            chunk = blob.get_chunk(self.version, self.max_chunk_size, sync)
        except Exception, err:
            logger.exception(err)
            logger.warning("Couldn't get chunk for session %s" % session_id)
            self._data_blob_queue[session_id].pop(0) #ignoring blob
            self._queue_lock.release()
            return True

        self._outgoing_chunks[chunk] = blob
        self.__send_chunk(peer, peer_guid, chunk)

        if blob.is_complete():
            self._data_blob_queue[session_id].pop(0)
        if len(self._data_blob_queue[session_id]) == 0:
            del self._data_blob_queue[session_id]
        self._queue_lock.release()
        return True

    def __send_chunk(self, peer, peer_guid, chunk):
        # add local identifier to chunk
        if self._local_chunk_id is None:
            self._local_chunk_id = random.randint(1000, MAX_INT32)
        chunk.id = self._local_chunk_id
        self._local_chunk_id = chunk.next_id

        if chunk.require_ack() :
            self._add_pending_ack(chunk.ack_id)

        self._send_chunk(peer, peer_guid, chunk)

gobject.type_register(BaseP2PTransport)
