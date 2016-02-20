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

import base64
import urlparse

__all__ = ['ProxyInfos']

class ProxyInfos(object):
    """Contain informations needed to make use of a proxy.

        @ivar host: hostname of the proxy server.
        @ivar port: port used to connect to server.
        @ivar type: proxy type
        @ivar user: username to use for authentication.
        @ivar password: password to use for authentication.
        @undocumented __get_*, __set_*

        @since: 0.1"""
    
    def __init__(self, host='', port=0, type='http', user=None, password=None):
        """Initializer
            
            @param host: the hostname of the proxy server.
            @type host: string
            
            @param port: the port used to connect to server.
            @type port: integer >= 0 and < 65536

            @param type: proxy type
            @type type: string in ('http', 'https', 'socks4', 'socks5')

            @param user: the username to use for authentication.
            @type user: string
            
            @param password: the password to use for authentication.
            @type password: string"""
        self.host = host
        self.port = port
        self.type = type
        self.user = user
        self.password = password
    
    @staticmethod
    def from_string(url, default_type='http'):
        """Builds a new L{ProxyInfos} instance from a given proxy url string
            @param url: the proxy url string
            @type url: string
            
            @param default_type: the default proxy type
            @type default_type: string in ('http', 'https', 'socks4', 'socks5')

            @return: L{ProxyInfos} instance filled with the infos given in the
                url"""
        # scheme://netloc/path;parameters?query#fragment
        # (scheme, netloc, path;parameters, query, fragment)
        url = urlparse.urlsplit(url, default_type)
        proxy_type = url[0]
        location = url[1]
        location = location.rsplit('@',1)
        if len(location) == 1:
            auth = ('','')
            host = location[0]
        else:
            auth = location[0].split(':',1)
            host = location[1]
        host = host.split(':',1)
        if len(host) == 1:
            port = 8080
        else:
            port = int(host[1])
        host = host[0]
        return ProxyInfos(host, port, proxy_type, auth[0], auth[1])

    def __get_port(self):
        return self._port
    def __set_port(self, port):
        self._port = int(port)
        assert(self._port >= 0 and self._port <= 65535)
    port = property(__get_port, __set_port, doc="Port used to connect to server.")

    def __get_type(self):
        return self._type
    def __set_type(self, type):
        assert(type in ('http', 'https', 'socks', 'socks4', 'socks5'))
        self._type = type
    type = property(__get_type, __set_type, doc="Proxy type.")

    def __str__(self):
        host = '%s:%u' % (self.host, self.port)
        if self.user:
            auth = '%s:%s' % (self.user, self.password)
            host = auth + '@' + host
        return self.type + '://' + host + '/'
    
    def __repr__(self):
        host = '%s:%u' % (self.host, self.port)
        if self.user:
            auth = '%s:%s' % (self.user, "*" * len(self.password))
            host = auth + '@' + host
        return self.type + '://' + host + '/'
