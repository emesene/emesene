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

from papyon.gnet.constants import *
from papyon.gnet.io import *
from papyon.msnp.message import MessageAcknowledgement
from papyon.msnp2p.constants import *
from papyon.msnp2p.transport.TLP import MessageChunk
from papyon.msnp2p.transport.base import BaseP2PTransport
import papyon.util.debug as debug

import gobject
import random
import struct
import logging
import socket
import uuid

__all__ = ['DirectP2PTransport']

logger = logging.getLogger('papyon.msnp2p.transport.direct')


class DirectP2PTransport(BaseP2PTransport):

    __gsignals__ = {
            "listening": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object, object))
    }

    def __init__(self, client, peer, peer_guid, transport_manager, ip=None,
            port=None, nonce=None):
        BaseP2PTransport.__init__(self, transport_manager, "direct")

        if ip is None:
            ip = client.local_ip
        if port is None:
            port = DEFAULT_DIRECT_PORT
        if nonce is None:
            nonce = str(uuid.uuid4())

        self._client = client
        self._peer = peer
        self._peer_guid = peer_guid
        self._nonce = nonce
        self._ip = ip
        self._port = port
        self._server = False
        self._listening = False
        self._connected = False
        self._extern_port = None
        self._mapping_timeout_src = None
        self._connect_timeout_src = None

        self.__pending_size = None
        self.__pending_chunk = ""
        self.__foo_sent = False
        self.__foo_received = False
        self.__nonce_sent = False
        self.__nonce_received = False

    @staticmethod
    def handle_peer(client, peer, peer_guid, transport_manager):
        return DirectP2PTransport(client, peer, peer_guid, transport_manager)

    @property
    def name(self):
        return "direct"

    @property
    def protocol(self):
        return "TCPv1"

    @property
    def peer(self):
        return self._peer

    @property
    def peer_guid(self):
        return self._peer_guid

    @property
    def connected(self):
        return self._connected

    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port

    @property
    def nonce(self):
        return self._nonce

    @property
    def rating(self):
        return 1

    @property
    def max_chunk_size(self):
        return 1350

    def open(self):
        self._server = False
        self._listening = False
        self._transport = TCPClient(self._ip, self._port)
        self._transport.connect("notify::status", self._on_status_changed)
        self._transport.connect("error", self._on_error)
        self._transport.connect("received", self._on_data_received)
        logger.info("Try to connect to %s(%i)" % (self._ip, self._port))
        self._connect_timeout_src = gobject.timeout_add(5000, self._on_connect_timeout)
        self._transport.open()

    def listen(self):
        self._server = True
        self._listening = False
        self._socket = self._open_listener()
        self._socket.setblocking(False)
        self._channel = gobject.IOChannel(self._socket.fileno())
        self._channel.set_flags(self._channel.get_flags() | gobject.IO_FLAG_NONBLOCK)
        self._channel.add_watch(gobject.IO_IN, self._on_listener_connected)

    def close(self):
        if hasattr(self, '_transport'):
            self._transport.close()
        self._remove_connect_timeout()
        self._remove_mapping_timeout()
        self._unmap_external_port()
        BaseP2PTransport.close(self)

    def _open_listener(self):
        s = socket.socket()
        while True:
            try:
                s.bind(("", self._port))
                s.listen(1)
            except Exception, err:
                self._port += 1
                continue
            else:
                break

        self._map_external_port(self._ip, self._port)
        return s

    def _map_external_port(self, local_ip, local_port, timeout=5):
        try:
            from gupnp.igd import Simple
        except ImportError:
            logger.error("Module gupnp.idg was not found")
            logger.error("Please install gupnp-igd >= 0.1.6 to get NAT traversal functionality")
            self._set_listening(None, None)
            return

        self._mapping_timeout_src = gobject.timeout_add(timeout * 1000,
                self._on_mapping_timeout)

        self.simple = Simple()
        self.simple.connect("error-mapping-port", self._on_error_mapping_port)
        self.simple.connect("mapped-external-port", self._on_external_port_mapped)
        self.simple.add_port("TCP", 0, local_ip, local_port, 6000, "MSN P2P Direct Connection")
        logger.info("Trying to map external port using UPnP")

    def _unmap_external_port(self):
        if not self._extern_port:
            return
        self.simple.remove_port("TCP", self._extern_port)
        self._extern_port = None

    def _remove_mapping_timeout(self):
        if self._mapping_timeout_src is not None:
            gobject.source_remove(self._mapping_timeout_src)
            self._mapping_timeout_src = None

    def _on_error_mapping_port(self, simple, error, proto, extern_port,
        local_ip, local_port, description):
        logger.warning("Error mapping port %u (%s)" % (local_port, error))
        print extern_port, local_ip, local_port, description
        self._set_listening(None, None)

    def _on_external_port_mapped(self, simple, proto, extern_ip, replaces,
        extern_port, local_ip, local_port, description):
        logger.info("External port %u mapped to local port %u" % (extern_port, local_port))
        self._extern_port = extern_port
        self._set_listening(extern_ip, extern_port)

    def _on_mapping_timeout(self):
        logger.warning("Error mapping port %u (timeout)" % self._port)
        self._mapping_timeout_src = None
        self._set_listening(None, None)
        return False

    def _set_listening(self, ip, port):
        if not ip or ip == "0.0.0.0":
            ip = self._client.client_ip
        if not port:
            port = self._port
        self._remove_mapping_timeout()
        if not self._listening:
            self._listening = True
            self.emit("listening", ip, port)

    def _send_chunk(self, chunk):
        self._send_data(str(chunk), self.__on_chunk_sent, (chunk,))

    def __on_chunk_sent(self, chunk):
        logger.debug(">> Chunk of %i bytes with flags 0x%x" %
                (chunk.header.chunk_size, chunk.header.flags))
        self._on_chunk_sent(chunk)

    def _send_data(self, data, callback=None, cb_args=()):
        body = struct.pack('<L', len(data)) + data
        self._transport.send(body, callback, *cb_args)

    def _remove_connect_timeout(self):
        if self._connect_timeout_src is not None:
            gobject.source_remove(self._connect_timeout_src)
            self._connect_timeout_src = None

    def _on_status_changed(self, transport, param):
        status = transport.get_property("status")
        if status == IoStatus.OPENING:
            return

        self._remove_connect_timeout()

        if status == IoStatus.OPEN:
            logger.info("Socket connection opened")
            if not self._server:
                self._handshake()
        elif status == IoStatus.CLOSED:
            logger.info("Socket connection closed")
            self._listening = False
            self._connected = False

    def _on_connect_timeout(self):
        logger.info("Socket connection timeout")
        self._on_failed()
        return False

    def _on_error(self, transport, error):
        logger.info("Socket connection failed")
        self._on_failed()

    def _on_failed(self):
        self.emit("failed")
        self.close()

    def _on_listener_connected(self, channel, condition):
        logger.debug("Peer connected to %s(%i)" % (self._ip, self._port))
        socket = self._socket.accept()[0]
        self._socket.close()
        self._socket = None
        self._transport = TCPClient(self._ip, self._port)
        self._transport.connect("notify::status", self._on_status_changed)
        self._transport.connect("received", self._on_data_received)
        self._transport.set_socket(socket)

    def _handshake(self):
        self._send_foo()
        self._send_nonce()

    def _send_foo(self):
        logger.debug("Sending FOO packet")
        self.__foo_sent = True
        self._send_data("foo\x00")

    def _receive_foo(self, chunk):
        self.__foo_received = True

    def _send_nonce(self):
        logger.debug("Sending nonce %s" % self._nonce)
        self.__nonce_sent = True
        chunk = MessageChunk()
        chunk.header.blob_id = random.randint(1000, 2147483647)
        chunk.set_nonce(self._nonce)
        self._send_data(str(chunk))

    def _receive_nonce(self, chunk):
        if not chunk.is_nonce_chunk():
            return
        nonce = chunk.get_nonce().upper()
        logger.debug("Received nonce %s" % nonce)
        if self._nonce.upper() != nonce:
            logger.warning("Received nonce doesn't match (connection failed)")
            self._on_failed()
            return
        self.__nonce_received = True
        if not self.__nonce_sent:
            self._send_nonce()
        logger.debug("Connected")
        self._connected = True
        self.emit("connected")

    def _on_data_received(self, transport, chunk, length):
        self.__pending_chunk += chunk

        while self.__pending_chunk:
            if self.__pending_size is None:
                if len(self.__pending_chunk) < 4:
                    return
                self.__pending_size = struct.unpack('<L', self.__pending_chunk[:4])[0]
                self.__pending_chunk = self.__pending_chunk[4:]
            if len(self.__pending_chunk) < self.__pending_size:
                return

            body = self.__pending_chunk[:self.__pending_size]
            self.__pending_chunk = self.__pending_chunk[self.__pending_size:]
            self.__pending_size = None

            if self._server and not self.__foo_received:
                self._receive_foo(body)
                return

            chunk = MessageChunk.parse(body)
            if not self.__nonce_received:
                self._receive_nonce(chunk)
            elif chunk.body == "\x00" *4:
                logger.debug("Received 0000 chunk, ignoring it")
            else:
                logger.debug("<< Chunk of %i bytes" % chunk.header.chunk_size)
                self._on_chunk_received(chunk)

