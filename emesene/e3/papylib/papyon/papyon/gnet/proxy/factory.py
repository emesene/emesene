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

from HTTPConnect import *
from SOCKS4 import *
from SOCKS5 import *

def ProxyFactory(client, proxies, preferred='direct'):
    if not proxies or preferred not in proxies or not proxies[preferred]:
        return client

    proxy = proxies[preferred]
    if proxy.type == 'http':
        return HTTPConnectProxy(client, proxy)
    elif proxy.type == 'https':
        return HTTPConnectProxy(client, proxy)
    elif proxy.type in ('socks', 'socks5'):
        # FIXME we assume "socks://" is a SOCKS5 proxy
        return SOCKS5Proxy(client, proxy)
    elif proxy.type == 'socks4':
        return SOCKS4Proxy(client, proxies['socks4'])
    else:
        return client
