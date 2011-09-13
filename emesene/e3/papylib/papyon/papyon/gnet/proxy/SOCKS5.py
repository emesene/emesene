# -*- coding: utf-8 -*-
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

from abstract import AbstractProxy
from papyon.gnet.io import TCPClient
from papyon.gnet.constants import *
from papyon.gnet.errors import *
from papyon.gnet.parser import DelimiterParser

import gobject
import logging
import socket
import struct

__all__ = ['SOCKS5Proxy']

logger = logging.getLogger('papyon.proxy.SOCKS5')

class SOCKS5Proxy(AbstractProxy):

    VERSION = 5
    CMD_CONNECT = 0x01
    AUTH_VERSION = 1
    MAX_LEN = 255
    RESERVED = 0x00

    AUTH_NONE = 0x00
    AUTH_GSSAPI = 0x01
    AUTH_USR_PASS = 0x02
    AUTH_NO_ACCEPT = 0xff

    ATYP_IPV4 = 0x01
    ATYP_DOMAINNAME = 0x03
    ATYP_IPV6 = 0x04

    STATE_NEGO = 0x01
    STATE_AUTH = 0x02
    STATE_CONN = 0x03
    STATE_RECV_IPV4_ADDR = 0x04
    STATE_RECV_ADDR_LEN = 0x05
    STATE_RECV_DOMAINNAME = 0x06

    CODE_SUCCEEDED = 0x00
    CODE_SRV_FAILURE = 0x01
    CODE_NOT_ALLOWED = 0x02
    CODE_NET_UNREACH = 0x03
    CODE_HOST_UNREACH = 0x04
    CODE_REFUSED = 0x05
    CODE_TTL_EXPIRED = 0x06
    CODE_CMD_NOT_SUP = 0x07
    CODE_ATYPE_NOT_SUP = 0x08

    NEGO_REPLY_LEN = 2
    AUTH_REPLY_LEN = 2
    CONN_REPLY_LEN = 4
    IPV4_ADDR_LEN = 4

    """Proxy class used to communicate with SOCKS5 proxies."""
    def __init__(self, client, proxy):
        assert(proxy.type in ('socks', 'socks5')), \
                "SOCKS5Proxy expects a socks5 proxy description"
        assert(client.domain == AF_INET), \
                "SOCKS5 CONNECT only handles INET address family"
        assert(client.type == SOCK_STREAM), \
                "SOCKS5 CONNECT only handles SOCK_STREAM"
        assert(client.status == IoStatus.CLOSED), \
                "SOCKS5Proxy expects a closed client"
        AbstractProxy.__init__(self, client, proxy)

        self._transport = TCPClient(self._proxy.host, self._proxy.port)
        self._transport.connect("notify::status", self._on_transport_status)
        self._transport.connect("error", self._on_transport_error)

        self._delimiter_parser = DelimiterParser(self._transport)
        self._delimiter_parser.connect("received", self._on_proxy_response)

        self._state = None
        self._must_auth = False

    # Opening state methods
    def _pre_open(self, io_object=None):
        AbstractProxy._pre_open(self)

    def _post_open(self):
        AbstractProxy._post_open(self)
        self._delimiter_parser.enable()
        self._send_nego_msg()
        
    # Public API
    @property
    def protocol(self):
        return "SOCKS5"

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
        self._client.send(buffer, callback, errback)

    # Handshake
    def _send_nego_msg(self):
        user = self._proxy.user
        password = self._proxy.password

        methods = [self.AUTH_NONE]
        if user or password:
            methods.append(self.AUTH_USR_PASS)

        msg = struct.pack('!BB', SOCKS5Proxy.VERSION,
                len(methods))
        for method in methods:
            msg += struct.pack('B', method)

        logger.info("Sending negotiation request (%i methods)" % len(methods))
        self._state = SOCKS5Proxy.STATE_NEGO
        self._delimiter_parser.delimiter = SOCKS5Proxy.NEGO_REPLY_LEN
        self._transport.send(msg)
        return True

    def _parse_nego_reply(self, response):
        version, method = struct.unpack('!BB', response[0:2])
        if version != SOCKS5Proxy.VERSION:
            raise Exception("Server is not SOCKS5 compatible")
        if method == SOCKS5Proxy.AUTH_NO_ACCEPT:
            raise Exception("Server doesn't support any of the proposed \
                    authentication methods")

        logger.info("Server chose authentication method %i" % method)
        self._must_auth = (method == SOCKS5Proxy.AUTH_USR_PASS)
        return True

    def _send_auth_msg(self):
        user = self._proxy.user
        password = self._proxy.password

        if len(user) > self.MAX_LEN or len(password) > self.MAX_LEN:
            raise Exception("User and password need to be less than %i \
                    characters long" % self.MAX_LEN)

        msg = struct.pack('B', SOCKS5Proxy.AUTH_VERSION)
        msg += struct.pack('B', len(user))
        if user:
            msg += user
        msg += struct.pack('B', len(password))
        if password:
            msg += password

        logger.info("Sending authentication request")
        self._state = SOCKS5Proxy.STATE_AUTH
        self._delimiter_parser.delimiter = SOCKS5Proxy.AUTH_REPLY_LEN
        self._transport.send(msg)

    def _check_auth_status(self, response):
        version, code = struct.unpack('!BB', response[0:2])
        if (version != SOCKS5Proxy.VERSION or
            code != SOCKS5Proxy.CODE_SUCCEEDED):
            raise Exception("Authentication didn't succeed (%s)" % code)
        logger.info("Authentication succeeded")
        return True

    def _send_connect_msg(self):
        msg = struct.pack('!BBB', SOCKS5Proxy.VERSION,
                SOCKS5Proxy.CMD_CONNECT, SOCKS5Proxy.RESERVED)
        try:
            addr = socket.inet_aton(self.host)
            msg += struct.pack('!BI', SOCKS5Proxy.ATYP_IPV4, addr)
        except:
            if len(self.host) > SOCKS5Proxy.MAX_LEN:
                raise Exception("Hostname is longer than max allowed length")
            msg += struct.pack('!BB', SOCKS5Proxy.ATYP_DOMAINNAME, len(self.host))
            msg += self.host

        msg += struct.pack('!H', self.port)

        logger.info("Connection request to %s:%u" % (self.host, self.port))
        self._state = SOCKS5Proxy.STATE_CONN
        self._delimiter_parser.delimiter = SOCKS5Proxy.CONN_REPLY_LEN
        self._transport.send(msg)

    def _parse_connect_reply(self, response):
        version, code, reserved, atyp = struct.unpack('!BBBB', response[0:4])
        if version != SOCKS5Proxy.VERSION or reserved != SOCKS5Proxy.RESERVED:
            raise Exception("Connection reply isn't SOCKS5 compatible")
        if code == SOCKS5Proxy.CODE_SUCCEEDED:
            logger.info("Connection request has been accepted")
        else:
            raise Exception("Connection request has been declined (%i)" % code)

        if atyp == SOCKS5Proxy.ATYP_IPV4:
            self._state = SOCKS5Proxy.STATE_RECV_IPV4_ADDR
            self._delimiter_parser.delimiter = SOCKS5Proxy.IPV4_ADDR_LEN
        elif atyp == SOCKS5Proxy.ATYP_DOMAINNAME:
            self._state = SOCKS5Proxy.STATE_RECV_ADDR_LEN
            self._delimiter_parser.delimiter = 1
        else:
            raise Exception('Unsupported address type: %i' % atyp)

    def _parse_domain_name_length(self, response):
        length, = struct.unpack('!B', response)
        self._state = SOCKS5Proxy.STATE_RECV_DOMAINNAME
        self._delimiter_parser.delimiter = length

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
        try:
            if self._state == SOCKS5Proxy.STATE_NEGO:
                self._parse_nego_reply(response)
                if self._must_auth:
                    self._send_auth_msg()
                else:
                    self._send_connect_msg()
            elif self._state == SOCKS5Proxy.STATE_AUTH:
                self._check_auth_status(response)
                self._send_connect_msg()
            elif self._state == SOCKS5Proxy.STATE_CONN:
                self._parse_connect_reply(response)
            elif self._state == SOCKS5Proxy.STATE_RECV_ADDR_LEN:
                self._parse_domain_name_length(response)
            elif (self._state == SOCKS5Proxy.STATE_RECV_IPV4_ADDR or
                  self._state == SOCKS5Proxy.STATE_RECV_DOMAINNAME):
                self._delimiter_parser.disable()
                self._transport.disable()
                self._client._proxy_open()
        except Exception, err:
            logger.error("Handshake failed")
            logger.exception(err)
            self.close()
            self.emit("error", SOCKS5Error(self, str(err)))
        return False

gobject.type_register(SOCKS5Proxy)
