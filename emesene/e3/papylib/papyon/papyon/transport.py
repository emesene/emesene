# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2005-2006 Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2006  Johann Prieur <johann.prieur@gmail.com>
# Copyright (C) 2006  Ole André Vadla Ravnås <oleavr@gmail.com>
# Copyright (C) 2010  Collabora Ltd.
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

"""Network Transport Layer

This module provides an abstraction of the transport to be used to communicate
with the MSN servers, actually MSN servers can communicate either through
direct connection using TCP/1863 or using TCP/80 by tunelling the protocol
inside HTTP POST requests.

The classes of this module are structured as follow:
G{classtree BaseTransport}"""

from gnet.proxy.factory import ProxyFactory
from papyon.util.async import run

import gnet
import gnet.protocol
import msnp

import logging
import gobject

__all__=['ServerType', 'DirectConnection']

logger = logging.getLogger('papyon.transport')

class ServerType(object):
    SWITCHBOARD = 'SB'
    NOTIFICATION = 'NS'

TransportError = gnet.IoError

class BaseTransport(gobject.GObject):
    """Abstract Base Class that modelize a connection to the MSN service, this
    abstraction is used to build various transports that expose the same
    interface, basically a transport is created using its constructor then it
    simply emits signals when network events (or even abstracted network events)
    occur, for example a Transport that successfully connected to the MSN
    service will emit a connection-success signal, and when that transport
    received a meaningful message it would emit a command-received signal.
        
        @ivar server: the server being used to connect to
        @type server: tuple(host, port)
        
        @ivar server_type: the server that we are connecting to, either
            Notification or switchboard.
        @type server_type: L{ServerType}

        @ivar proxies: proxies that we can use to connect
        @type proxies: dict(type => L{gnet.proxy.ProxyInfos})
        
        @ivar transaction_id: the current transaction ID
        @type transaction_id: integer


        @cvar connection-failure: signal emitted when the connection fails
        @type connection-failure: ()

        @cvar connection-success: signal emitted when the connection succeed
        @type connection-success: ()

        @cvar connection-reset: signal emitted when the connection is being
        reset
        @type connection-reset: ()

        @cvar connection-lost: signal emitted when the connection was lost
        @type connection-lost: ()

        @cvar command-received: signal emitted when a command is received
        @type command-received: FIXME

        @cvar command-sent: signal emitted when a command was successfully
            transmitted to the server
        @type command-sent: FIXME

        @undocumented: __gsignals__"""
    
    __gsignals__ = {
            "connection-failure" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "connection-success" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),

            "connection-reset" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),

            "connection-lost" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "command-received": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "command-sent": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            }   

    def __init__(self, server, server_type=ServerType.NOTIFICATION, proxies={}):
        """Connection initialization
        
            @param server: the server to connect to.
            @type server: (host: string, port: integer)

            @param server_type: the server that we are connecting to, either
                Notification or switchboard.
            @type server_type: L{ServerType}

            @param proxies: proxies that we can use to connect
            @type proxies: {type: string => L{gnet.network.ProxyInfos}}"""
        gobject.GObject.__init__(self)
        self.server = server
        self.server_type = server_type
        self.proxies = proxies
        self._transaction_id = 0
   
    @property
    def transaction_id(self):
        return self._transaction_id

    # Connection
    def establish_connection(self):
        """Connect to the server server"""
        raise NotImplementedError

    def lose_connection(self, error=None):
        """Disconnect from the server
        
            @param error: the error that caused the disconnection if any
            @type error: Exception"""
        raise NotImplementedError

    def reset_connection(self, server=None):
        """Reset the connection

            @param server: when set, reset the connection and
                connect to this new server
            @type server: tuple(host, port)"""
        raise NotImplementedError

    # Command Sending
    def send_command(self, command, increment=True, callback=None,
            errback=None):
        """
        Sends a L{msnp.Command} to the server.

            @param command: command to send
            @type command: L{msnp.Command}

            @param increment: if False, the transaction ID is not incremented
            @type increment: bool

            @param callback: callback once transmission of command succeeded
            @type callback: tuple (callable, args)

            @param errback: callback if transmission of command failed
            @type errback: tuple (callable, args)
        """
        raise NotImplementedError

    def send_command_ex(self, command, arguments=(), payload=None,
            increment=True, callback=None, errback=None):
        """
        Builds a command object then send it to the server.
        
            @param command: the command name, must be a 3 letters
                uppercase string.
            @type command: string
        
            @param arguments: command arguments
            @type arguments: (string, ...)
        
            @param payload: payload data
            @type payload: string

            @param increment: if False, the transaction ID is not incremented
            @type increment: bool

            @param callback: callback once transmission of command succeeded
            @type callback: tuple (callable, args)

            @param errback: callback if transmission of command failed
            @type errback: tuple (callable, args)
        """
        cmd = msnp.Command()
        cmd.build(command, self._transaction_id, payload, *arguments)
        self.send_command(cmd, increment, callback, errback)
        return cmd

    def enable_ping(self):
        pass

    def _increment_transaction_id(self):
        """Increments the Transaction ID then return it.
            
            @rtype: integer"""
        self._transaction_id += 1
        return self._transaction_id
gobject.type_register(BaseTransport)


class DirectConnection(BaseTransport):
    """Implements a direct connection to the net using TCP/1863"""

    def __init__(self, server, server_type=ServerType.NOTIFICATION, proxies={}):
        BaseTransport.__init__(self, server, server_type, proxies)

        transport = self._setup_transport(server[0], server[1], proxies)
        receiver = gnet.parser.DelimiterParser(transport)
        receiver.connect("received", self.__on_received)

        self._receiver = receiver
        self._receiver.delimiter = "\r\n"
        self._transport = transport
        self.__pending_command = None
        self.__resetting = False
        self.__error = None

    __init__.__doc__ = BaseTransport.__init__.__doc__

    def _setup_transport(self, host, port, proxies):
        transport = gnet.io.TCPClient(host, port)
        if proxies:
            transport = ProxyFactory(transport, proxies, 'direct')
        transport.connect("notify::status", self.__on_status_change)
        transport.connect("error", self.__on_error)
        return transport

    ### public commands

    @property
    def sockname(self):
        return self._transport.sockname

    def establish_connection(self):
        self.__pending_command = None
        logger.debug('<-> Connecting to %s:%d' % self.server )
        self._transport.open()

    def lose_connection(self, error=None):
        self.__error = error
        if error is not None:
            self.emit("connection-failure", error)

        self.__resetting = False
        self._transport.close()

    def reset_connection(self, server=None):
        if server:
            self._transport.set_property("host", server[0])
            self._transport.set_property("port", server[1])
            self.server = server
        self.__resetting = True
        self._transport.close()
        self._transport.open()

    def send_command(self, command, increment=True, callback=None,
            errback=None):
        if self.__error:
            logger.warning("Transport is errored, not sending %s" % command.name)
            run(errback, self.__error)
            return
        logger.debug('>>> ' + unicode(command))
        self._transport.send(str(command),
                (self.__on_command_sent, command, callback), errback)
        if increment:
            self._increment_transaction_id()

    def enable_ping(self):
        cmd = msnp.Command()
        cmd.build("PNG", None)
        self.send_command(cmd, False)

    def __on_command_sent(self, command, user_callback):
        self.emit("command-sent", command)
        run(user_callback)

    ### callbacks
    def __on_status_change(self, transport, param):
        status = transport.get_property("status")
        if status == gnet.IoStatus.OPEN:
            if self.__resetting:
                self.emit("connection-reset")
                self.__resetting = False
            self.emit("connection-success")
        elif status == gnet.IoStatus.CLOSED:
            if not self.__resetting and not self.__error:
                self.emit("connection-lost", None)
            self.__error = None
    
    def __on_error(self, transport, error):
        status = transport.get_property("status")
        self.__error = error
        if status == gnet.IoStatus.OPEN:
            self.emit("connection-lost", error)
        else:
            self.emit("connection-failure", error)

    def __on_received(self, receiver, chunk):
        if self.__pending_command is None:
            cmd = msnp.Command()
            try:
                cmd.parse(chunk)
            except Exception, err:
                logger.error("Received invalid command, closing connection")
                self.lose_connection(err)
                return
            if cmd.payload_len > 0:
                self.__pending_command = cmd
                self._receiver.delimiter = cmd.payload_len
                return # wait for payload
        else:
            cmd = self.__pending_command
            cmd.payload = chunk
            self.__pending_command = None
            self._receiver.delimiter = "\r\n"
        logger.debug('<<< ' + unicode(cmd))
        self.emit("command-received", cmd)
gobject.type_register(DirectConnection)


class HTTPPollConnection(BaseTransport):
    """Implements an HTTP polling transport, basically it encapsulates the MSNP
    commands into an HTTP request, and receive responses by polling a specific
    url"""
    def __init__(self, server, server_type=ServerType.NOTIFICATION, proxies={}):
        self._target_server = server
        if server_type == ServerType.SWITCHBOARD:
            server = (server[0], 80)
        else:
            server = ("gateway.messenger.hotmail.com", 80)
        BaseTransport.__init__(self, server, server_type, proxies)
        self._setup_transport(server[0], server[1], proxies)
        
        self._command_queue = []
        self._waiting_for_response = False # are we waiting for a response
        self._session_id = None
        self.__error = None

    def _setup_transport(self, host, port, proxies):
        handles = []
        transport = gnet.protocol.HTTP(host, port, proxies)
        handles.append(transport.connect("response-received", self.__on_received))
        handles.append(transport.connect("request-sent", self.__on_sent))
        handles.append(transport.connect("error", self.__on_error))
        self._transport_handles = handles
        self._transport = transport

    def establish_connection(self):
        logger.debug('<-> Connecting to %s:%d' % self.server)
        self._polling_source_id = gobject.timeout_add_seconds(5, self._poll)
        self.emit("connection-success")

    def lose_connection(self, error=None):
        gobject.source_remove(self._polling_source_id)
        del self._polling_source_id
        if error is not None:
            self.emit("connection-failure", error)
        elif not self.__error:
            self.emit("connection-lost", None)
        self.__error = None

    def reset_connection(self, server=None):
        if server:
            self._target_server = server
        self.emit("connection-reset")

    def change_gateway(self, server):
        if self.server == server:
            return
        logger.debug('<-> Changing gateway to %s:%d' % server)
        self.server = server
        for handle in self._transport_handles:
            self._transport.disconnect(handle)
        self._transport.close()
        self._setup_transport(server[0], server[1], self.proxies)

    def send_command(self, command, increment=True, callback=None,
            errback=None):
        self._command_queue.append((command, increment, callback, errback))
        self._send_command()

    def _send_command(self):
        if len(self._command_queue) == 0 or self._waiting_for_response:
            return
        command, increment = self._command_queue[0][0:2]
        resource = "/gateway/gateway.dll"
        headers = {
            "Accept": "*/*",
            "Accept-Language": "en-us",
            #"User-Agent": "MSMSGS",
            "Connection": "Keep-Alive",
            "Pragma": "no-cache",
            "Content-Type": "application/x-msn-messenger",
            "Proxy-Connection": "Keep-Alive"
        }
        
        str_command = str(command)
        if self._session_id is None:            
            resource += "?Action=open&Server=%s&IP=%s" % (self.server_type,
                    self._target_server[0])
        elif command == None:# Polling the server for queued messages
            resource += "?Action=poll&SessionID=%s" % self._session_id 
            str_command = ""
        else:
            resource += "?SessionID=%s" % self._session_id

        self._transport.request(resource, headers, str_command, "POST")
        self._waiting_for_response = True
        
        if command is not None:
            logger.debug('>>> ' + unicode(command))
        
        if increment:
            self._increment_transaction_id()
        
    def _poll(self):
        if not self._waiting_for_response:
            self.send_command(None)
        return True
    
    def __on_error(self, transport, error):
        self.__error = error
        self.emit("connection-lost", error)
        self.lose_connection()
        
    def __on_received(self, transport, http_response):
        if 'X-MSN-Messenger' in http_response.headers:
            data = http_response.headers['X-MSN-Messenger'].split(";")
            for elem in data:
                key, value =  [p.strip() for p in elem.split('=', 1)]
                if key == 'SessionID':
                    self._session_id = value
                elif key == 'GW-IP':
                    self.change_gateway((value, self.server[1]))
                elif key == 'Session'and value == 'close':
                    #self.lose_connection()
                    pass
        
        self._waiting_for_response = False

        commands = http_response.body
        while len(commands) != 0:
            commands = self.__extract_command(commands)
        
        self._send_command()

    def __on_sent(self, transport, http_request):
        if len(self._command_queue) == 0:
            return
        command, increment, callback, errback = self._command_queue.pop(0)
        if command is not None:
            run(callback)
            self.emit("command-sent", command)

    def __extract_command(self, data):
        try:
            first, rest = data.split('\r\n', 1)
        except ValueError, err:
            logger.warning('Unable to extract a command: %s' % data)
            self.lose_connection(err)
            return []

        try:
            cmd = msnp.Command()
            cmd.parse(first.strip())
            if cmd.payload_len > 0:
                cmd.payload = rest[:cmd.payload_len].strip()
                rest = rest[cmd.payload_len:]
        except Exception, err:
            logger.error("Received invalid command, closing connection")
            self.lose_connection(err)
            return []

        logger.debug('<<< ' + unicode(cmd))
        self.emit("command-received", cmd)
        return rest
