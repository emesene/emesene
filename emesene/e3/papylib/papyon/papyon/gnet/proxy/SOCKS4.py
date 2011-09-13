# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Johann Prieur <johann.prieur@gmail.com>
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

from abstract import AbstractProxy
from papyon.gnet.io import TCPClient
from papyon.gnet.constants import *
from papyon.gnet.errors import *
from papyon.gnet.parser import DelimiterParser

import gobject
import logging
import struct

__all__ = ['SOCKS4Proxy']

logger = logging.getLogger('papyon.proxy.SOCKS4')

class SOCKS4Proxy(AbstractProxy):

    PROTOCOL_VERSION = 4
    CONNECT_COMMAND = 1

    """Proxy class used to communicate with SOCKS4 proxies."""
    def __init__(self, client, proxy_infos):
        assert(proxy_infos.type == 'socks4'), \
                "SOCKS4Proxy expects a socks4 proxy description"
        # TODO : implement version 4a of the protocol to allow proxy-side name resolution
        assert(client.domain == AF_INET), \
                "SOCKS4 CONNECT only handles INET address family"
        assert(client.type == SOCK_STREAM), \
                "SOCKS4 CONNECT only handles SOCK_STREAM"
        assert(client.status == IoStatus.CLOSED), \
                "SOCKS4Proxy expects a closed client"
        AbstractProxy.__init__(self, client, proxy_infos)

        self._transport = TCPClient(self._proxy.host, self._proxy.port)
        self._transport.connect("notify::status", self._on_transport_status)
        self._transport.connect("error", self._on_transport_error)

        self._delimiter_parser = DelimiterParser(self._transport)
        self._delimiter_parser.delimiter = 8
        self._delimiter_parser.connect("received", self._on_proxy_response)

    # Opening state methods
    def _pre_open(self, io_object=None):
        AbstractProxy._pre_open(self)

    def _post_open(self):
        AbstractProxy._post_open(self)
        user = self._proxy.user

        proxy_protocol  = struct.pack('!BBH', SOCKS4Proxy.PROTOCOL_VERSION,
                SOCKS4Proxy.CONNECT_COMMAND, self.port)

        for part in self.host.split('.'):
           proxy_protocol += struct.pack('B', int(part))

        proxy_protocol += user
        proxy_protocol += struct.pack('B', 0)

        self._delimiter_parser.enable()
        self._transport.send(proxy_protocol)
        
    # Public API
    @property
    def protocol(self):
        return "SOCKS4"

    def open(self):
        """Open the connection."""
        if not self._configure():
            return
        self._pre_open()
        try:
            self._transport.open()
        except:
            pass

    def close(self):
        """Close the connection."""
        self._delimiter_parser.disable()
        self._client._proxy_closed()
        self._transport.close()

    def send(self, buffer, callback=None, errback=None):
        self._client.send(buffer, callback, errback=None)

    # Callbacks
    def _on_transport_status(self, transport, param):
        if transport.status == IoStatus.OPEN:
            self._post_open()
        elif transport.status == IoStatus.OPENING:
            self._client._proxy_opening(self._transport._transport)
            self._status = transport.status
        else:
            self._status = transport.status

    def _on_transport_error(self, transport, error):
        self.close()
        self.emit("error", error)

    def _on_proxy_response(self, parser, response):
        version, response_code = struct.unpack('BB', response[0:2])
        assert(version == 0)
        if self.status == IoStatus.OPENING:
            if response_code == 90:
                self._delimiter_parser.disable()
                self._transport.disable()
                self._client._proxy_open()
            else:
                logger.error("Connection failed (%s)" % response_code)
                self.close()
                self.emit("error", SOCKS4Error(self, response_code))
            return False

gobject.type_register(SOCKS4Proxy)
