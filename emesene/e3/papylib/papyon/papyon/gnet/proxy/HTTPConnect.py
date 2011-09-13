# -*- coding: utf-8 -*-
#
# Copyright (C) 2006  Ali Sabil <ali.sabil@gmail.com>
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
from papyon.gnet.parser import HTTPParser

import gobject
import base64
import logging

__all__ = ['HTTPConnectProxy']

logger = logging.getLogger('papyon.proxy.HTTP')

class HTTPConnectProxy(AbstractProxy):
    def __init__(self, client, proxy_infos):
        assert(proxy_infos.type in ('http', 'https')), "HTTPConnectProxy expects an http(s) proxy description"
        assert(client.domain == AF_INET), "HTTP CONNECT only handles INET address family"
        assert(client.type == SOCK_STREAM), "HTTP CONNECT only handles SOCK_STREAM"
        assert(client.status == IoStatus.CLOSED), "HTTPConnectProxy expects a closed client"
        AbstractProxy.__init__(self, client, proxy_infos)

        self._transport = TCPClient(self._proxy.host, self._proxy.port)
        self._transport.connect("notify::status", self._on_transport_status)
        self._transport.connect("error", self._on_transport_error)
        self._http_parser = HTTPParser(self._transport)
        self._http_parser.connect("received", self._on_proxy_response)

    # opening state methods
    def _pre_open(self, io_object=None):
        AbstractProxy._pre_open(self)

    def _post_open(self):
        AbstractProxy._post_open(self)
        proxy_protocol  = 'CONNECT %s:%s HTTP/1.1\r\n' % (self.host, self.port)
        proxy_protocol += 'Proxy-Connection: Keep-Alive\r\n'
        proxy_protocol += 'Pragma: no-cache\r\n'
        proxy_protocol += 'User-Agent: %s/%s\r\n' % (GNet.NAME, GNet.VERSION)
        if self._proxy.user:
            auth = base64.encodestring(self._proxy.user + ':' + self._proxy.password).strip()
            proxy_protocol += 'Proxy-authorization: Basic ' + auth + '\r\n'
        proxy_protocol += '\r\n'

        self._http_parser.enable()
        self._transport.send(proxy_protocol)

    # public API
    @property
    def protocol(self):
        return "HTTPConnect"

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
        self._http_parser.disable()
        self._client._proxy_closed()
        self._transport.close()

    def send(self, buffer, callback=None, errback=None):
        self._client.send(buffer, callback, errback=None)

    # callbacks and signal handlers
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
        if self.status == IoStatus.OPENING:
            if response.status == 200:
                self._http_parser.disable()
                self._transport.disable()
                self._client._proxy_open()
            elif response.status == 100:
                return True
            else:
                logger.error("Connection failed (%s)" % response.status)
                self.close()
                self.emit("error", HTTPConnectError(self, response.status))
            return False
gobject.type_register(HTTPConnectProxy)
