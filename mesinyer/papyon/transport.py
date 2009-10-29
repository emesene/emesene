# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2005-2006 Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2006  Johann Prieur <johann.prieur@gmail.com>
# Copyright (C) 2006  Ole André Vadla Ravnås <oleavr@gmail.com>
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

    def lose_connection(self):
        """Disconnect from the server"""
        raise NotImplementedError

    def reset_connection(self, server=None):
        """Reset the connection

            @param server: when set, reset the connection and
                connect to this new server
            @type server: tuple(host, port)"""
        raise NotImplementedError

    # Command Sending
    def send_command(self, command, increment=True, callback=None, *cb_args):
        """
        Sends a L{msnp.Command} to the server.

            @param command: command to send
            @type command: L{msnp.Command}

            @param increment: if False, the transaction ID is not incremented
            @type increment: bool

            @param callback: callback to be used when the command has been
                transmitted
            @type callback: callable

            @param cb_args: callback arguments
            @type cb_args: Any, ...
        """
        raise NotImplementedError

    def send_command_ex(self, command, arguments=(), payload=None, 
            increment=True, callback=None, *cb_args):
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

            @param callback: callback to be used when the command has been
                transmitted
            @type callback: callable

            @param cb_args: callback arguments
            @type cb_args: tuple
        """
        cmd = msnp.Command()
        cmd.build(command, self._transaction_id, payload, *arguments)
        self.send_command(cmd, increment, callback, *cb_args)
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

        transport = gnet.io.TCPClient(server[0], server[1])
        transport.connect("notify::status", self.__on_status_change)
        transport.connect("error", self.__on_error)

        receiver = gnet.parser.DelimiterParser(transport)
        receiver.connect("received", self.__on_received)

        self._receiver = receiver
        self._receiver.delimiter = "\r\n"
        self._transport = transport
        self.__pending_chunk = None
        self.__resetting = False
        self.__error = False
        self.__png_timeout = None

    __init__.__doc__ = BaseTransport.__init__.__doc__

    ### public commands

    @property
    def sockname(self):
        return self._transport.sockname

    def establish_connection(self):
        logger.debug('<-> Connecting to %s:%d' % self.server )
        self._transport.open()

    def lose_connection(self):
        self.__resetting = False
        self._transport.close()
        if self.__png_timeout is not None:
            gobject.source_remove(self.__png_timeout)
            self.__png_timeout = None

    def reset_connection(self, server=None):
        if server:
            self._transport.set_property("host", server[0])
            self._transport.set_property("port", server[1])
            self.server = server
        self.__resetting = True
        if self.__png_timeout is not None:
            gobject.source_remove(self.__png_timeout)
            self.__png_timeout = None
        self._transport.close()
        self._transport.open()

    def send_command(self, command, increment=True, callback=None, *cb_args):
        logger.debug('>>> ' + unicode(command))
        our_cb_args = (command, callback, cb_args)
        self._transport.send(str(command), self.__on_command_sent, *our_cb_args)
        if increment:
            self._increment_transaction_id()

    def enable_ping(self):
        cmd = msnp.Command()
        cmd.build("PNG", None)
        self.send_command(cmd, False)
        self.__png_timeout = None
        return False

    def __on_command_sent(self, command, user_callback, user_cb_args):
        self.emit("command-sent", command)
        if user_callback:
            user_callback(*user_cb_args)

    def __handle_ping_reply(self, command):
        timeout = int(command.arguments[0])
        self.__png_timeout = gobject.timeout_add(timeout * 1000, self.enable_ping)

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
            self.__error = False
    
    def __on_error(self, transport, reason):
        status = transport.get_property("status")
        self.__error = True
        if status == gnet.IoStatus.OPEN:
            self.emit("connection-lost", reason)
        else:
            self.emit("connection-failure", reason)

    def __on_received(self, receiver, chunk):
        cmd = msnp.Command()
        if self.__pending_chunk:
            chunk = self.__pending_chunk + "\r\n" + chunk
            cmd.parse(chunk)
            self.__pending_chunk = None
            self._receiver.delimiter = "\r\n"
        else:
            cmd.parse(chunk)
            if cmd.name in msnp.Command.INCOMING_PAYLOAD or \
                    (cmd.is_error() and (cmd.arguments is not None) and len(cmd.arguments) > 0):
                try:
                    payload_len = int(cmd.arguments[-1])
                except:
                    payload_len = 0
                if payload_len > 0:
                    self.__pending_chunk = chunk
                    self._receiver.delimiter = payload_len
                    return
        logger.debug('<<< ' + unicode(cmd))
        if cmd.name == 'QNG':
            self.__handle_ping_reply(cmd)
        else:
            self.emit("command-received", cmd)
gobject.type_register(DirectConnection)


class HTTPPollConnection(BaseTransport):
    """Implements an HTTP polling transport, basically it encapsulates the MSNP
    commands into an HTTP request, and receive responses by polling a specific
    url"""
    def __init__(self, server, server_type=ServerType.NOTIFICATION, proxies={}):
        self._target_server = server
        server = ("gateway.messenger.hotmail.com", 80)
        BaseTransport.__init__(self, server, server_type, proxies)
        self._setup_transport()
        
        self._command_queue = []
        self._waiting_for_response = False # are we waiting for a response
        self._session_id = None
        self.__error = False

    def _setup_transport(self):
        server = self.server
        proxies = self.proxies
        if 'http' in proxies:
            transport = gnet.protocol.HTTP(server[0], server[1], proxies['http'])
        else:
            transport = gnet.protocol.HTTP(server[0], server[1])
        transport.connect("response-received", self.__on_received)
        transport.connect("request-sent", self.__on_sent)
        transport.connect("error", self.__on_error)
        self._transport = transport

    def establish_connection(self):
        logger.debug('<-> Connecting to %s:%d' % self.server)
        self._polling_source_id = gobject.timeout_add(5000, self._poll)
        self.emit("connection-success")

    def lose_connection(self):
        gobject.source_remove(self._polling_source_id)
        del self._polling_source_id
        if not self.__error:
            self.emit("connection-lost", None)
        self.__error = False

    def reset_connection(self, server=None):
        if server:
            self._target_server = server
        self.emit("connection-reset")

    def send_command(self, command, increment=True, callback=None, *cb_args):
        self._command_queue.append((command, increment, callback, cb_args))
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
    
    def __on_error(self, transport, reason):
        self.__error = True
        self.emit("connection-lost", reason)
        
    def __on_received(self, transport, http_response):
        if http_response.status == 403:
            self.emit("connection-lost", TransportError.PROXY_FORBIDDEN)
            self.lose_connection()
        if 'X-MSN-Messenger' in http_response.headers:
            data = http_response.headers['X-MSN-Messenger'].split(";")
            for elem in data:
                key, value =  [p.strip() for p in elem.split('=', 1)]
                if key == 'SessionID':
                    self._session_id = value
                elif key == 'GW-IP':
                    self.server = (value, self.server[1])
                    self._setup_transport()
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
        command, increment, callback, cb_args = self._command_queue.pop(0)
        if command is not None:
            if callback:
                callback(*cb_args)
            self.emit("command-sent", command)

    def __extract_command(self, data):
        first, rest = data.split('\r\n', 1)
        cmd = msnp.Command()
        cmd.parse(first.strip())
        if cmd.name in msnp.Command.INCOMING_PAYLOAD or \
                (cmd.is_error() and (cmd.arguments is not None) and len(cmd.arguments) > 0):
            try:
                payload_len = int(cmd.arguments[-1])
            except:
                payload_len = 0
            if payload_len > 0:
                cmd.payload = rest[:payload_len].strip()
            logger.debug('<<< ' + unicode(cmd))
            self.emit("command-received", cmd)
            return rest[payload_len:]
        else:
            logger.debug('<<< ' + unicode(cmd))
            self.emit("command-received", cmd)
            return rest



