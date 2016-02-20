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

from papyon.errors import ClientError, ClientErrorType, ParseError

class IoError(ClientError):
    """I/O error codes"""
    UNKNOWN = 0

    CONNECTION_FAILED = 1
    CONNECTION_TIMED_OUT = 2
    CONNECTION_CLOSED = 3

    SSL_CONNECTION_FAILED = 10
    SSL_PROTOCOL_ERROR = 11

    PROXY_CONNECTION_FAILED = 20
    PROXY_AUTHENTICATION_REQUIRED = 21
    PROXY_FORBIDDEN = 22

    HOSTNAME_RESOLVE_FAILED = 30

    def __init__(self, code):
        ClientError.__init__(self, ClientErrorType.NETWORK, code)

    def __str__(self):
        return "I/O Error (%i)" % self._code

class IoConnectionFailed(IoError):
    def __init__(self, transport, details=""):
        IoError.__init__(self, IoError.CONNECTION_FAILED)
        self.transport = transport
        self._details = details

    def __str__(self):
        return "Connection to %s:%s (%s) failed: %s" % (self.transport.host,
                self.transport.port, self.transport.protocol, self._details)

class IoConnectionClosed(IoError):
    def __init__(self, transport, status):
        IoError.__init__(self, IoError.CONNECTION_CLOSED)
        self.transport = transport
        self.status = status

    def __str__(self):
        return "Connection to %s:%s (%s) is closed: %s" % (self.transport.host,
                self.transport.port, self.transport.protocol, self.status)


class SSLError(IoError):
    def __init__(self, details=""):
        IoError.__init__(self, IoError.SSL_CONNECTION_FAILED)
        self._details = details

    def __str__(self):
        return "SSL Error: %s" % self._details


class ProxyError(IoError):
    def __init__(self, proxy, code, details=""):
        IoError.__init__(self, code)
        self.proxy = proxy
        self._details = details

    def __str__(self):
        return "%s Proxy Error: %s" % (self.proxy.protocol, self._details)

class HTTPConnectError(ProxyError):
    def __init__(self, proxy, response):
        code = IoError.PROXY_CONNECTION_FAILED
        if response == 407:
            code = IoError.PROXY_AUTHENTICATION_REQUIRED
        ProxyError.__init__(self, proxy, code, str(response))

class SOCKS4Error(ProxyError):
    def __init__(self, proxy, response):
        code = IoError.PROXY_CONNECTION_FAILED
        if response in (92, 93):
            code = IoError.PROXY_AUTHENTICATION_REQUIRED
        ProxyError.__init__(self, proxy, code, str(response))

class SOCKS5Error(ProxyError):
    def __init__(self, proxy, details=""):
        code = IoError.PROXY_CONNECTION_FAILED
        ProxyError.__init__(self, proxy, code, details)


class HTTPError(IoError):
    def __init__(self, response):
        IoError.__init__(self, IoError.UNKNOWN)
        self.response = response

    def __str__(self):
        return "HTTP Error (%s): %s" % (self.response.status,
                self.response.reason)

class HTTPParseError(ParseError):
    def __init__(self, message):
        ParseError.__init__(self, "HTTP", message)
