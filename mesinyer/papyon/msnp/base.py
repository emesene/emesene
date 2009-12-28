# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2005-2006 Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2005-2006 Ole André Vadla Ravnås <oleavr@gmail.com> 
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

"""Base classes used by the specific classes of the Core Protocol"""

import logging

__all__ = ['BaseProtocol']

logger = logging.getLogger('papyon.protocol')

class ProtocolState(object):
    CLOSED = 0
    OPENING = 1
    AUTHENTICATING = 2
    AUTHENTICATED = 3
    SYNCHRONIZING = 4
    SYNCHRONIZED = 5
    OPEN = 6


class BaseProtocol(object):
    """Base class used to implement the Notification protocol as well
    as the Switchboard protocol
        @group Handlers: _handle_*, _default_handler, _error_handler

        @ivar _client: the parent instance of L{client.Client}
        @type _client: L{client.Client}

        @ivar _transport: the transport instance
        @type _transport: L{transport.BaseTransport}
    
        @ivar _proxies: a dictonary mapping the proxy type to a
            L{gnet.proxy.ProxyInfos} instance
    """

    def __init__(self, client, transport, proxies={}):
        """Initializer

            @param client: the parent instance of L{client.Client}
            @type client: L{client.Client}

            @param transport: The transport to use to speak the protocol
            @type transport: L{transport.BaseTransport}
            
            @param proxies: a dictonary mapping the proxy type to a
                L{gnet.proxy.ProxyInfos} instance
            @type proxies: {type: string, proxy:L{gnet.proxy.ProxyInfos}}
        """
        transport.connect("command-received", self._dispatch_command)
        transport.connect("connection-success", self._connect_cb)
        transport.connect("connection-failure", self._disconnect_cb)
        transport.connect("connection-lost", self._disconnect_cb)
        
        self._client = client
        self._transport = transport
        self._proxies = proxies

    def _send_command(self, command, arguments=(), payload=None, 
            increment=True, callback=None, *cb_args):
        command = self._transport.send_command_ex(command, arguments, payload, 
                                                increment, callback, *cb_args)
        return command.transaction_id
   
    # default handlers
    def _default_handler(self, command):
        """
        Default handler used when no handler is defined
        
            @param command: the received command
            @type command: L{command.Command}
        """
        logger.warning('Notification unhandled command : ' + unicode(command))

    def _error_handler(self, error):
        """Handles errors
        
            @param error: an error command object
            @type error: L{command.Command}
        """
        logger.error('Notification got error : ' + unicode(error))

    # callbacks
    def _dispatch_command(self, connection, command):
        if not command.is_error():
            handler = getattr(self,
                    '_handle_' + command.name,
                    self._default_handler)
            handler(command)
        else:
            self._error_handler(command)
   
    def _connect_cb(self, transport):
        pass

    def _disconnect_cb(self, transport, reason):
        pass
