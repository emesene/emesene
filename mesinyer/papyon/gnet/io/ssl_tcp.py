# -*- coding: utf-8 -*-
#
# Copyright (C) 2005  Ole André Vadla Ravnås <oleavr@gmail.com>
# Copyright (C) 2006-2007  Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2007  Johann Prieur <johann.prieur@gmail.com>
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
from papyon.gnet.constants import *
from papyon.gnet.proxy.proxyfiable import ProxyfiableClient
from ssl_socket import SSLSocketClient

import gobject

__all__ = ['SSLTCPClient']

class SSLTCPClient(SSLSocketClient, ProxyfiableClient):
    """Asynchronous TCP client class.

        @sort: __init__, open, send, close
        @undocumented: do_*, _watch_*, __io_*, _connect_done_handler

        @since: 0.1"""

    def __init__(self, host, port):
        """initializer

            @param host: the hostname to connect to.
            @type host: string

            @param port: the port number to connect to.
            @type port: integer > 0 and < 65536"""
        SSLSocketClient.__init__(self, host, port, AF_INET, SOCK_STREAM)
        ProxyfiableClient.__init__(self)
gobject.type_register(SSLTCPClient)
