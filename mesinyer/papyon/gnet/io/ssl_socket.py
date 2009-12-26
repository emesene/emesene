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
from iochannel import GIOChannelClient

import gobject
import socket
import OpenSSL.SSL as OpenSSL

__all__ = ['SSLSocketClient']

class SSLSocketClient(GIOChannelClient):
    """Asynchronous Socket client class.

        @sort: __init__, open, send, close
        @undocumented: do_*, _watch_*, __io_*, _connect_done_handler

        @since: 0.1"""

    def __init__(self, host, port, domain=AF_INET, type=SOCK_STREAM):
        GIOChannelClient.__init__(self, host, port, domain, type)

    def _pre_open(self, sock=None):
        if sock is None:
            sock = socket.socket(self._domain, self._type)
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            except AttributeError:
                pass
        context = OpenSSL.Context(OpenSSL.SSLv23_METHOD)
        ssl_sock = OpenSSL.Connection(context, sock)
        GIOChannelClient._pre_open(self, ssl_sock)

    def _post_open(self):
        GIOChannelClient._post_open(self)
        if self._transport.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR) == 0:
            self._watch_set_cond(gobject.IO_IN | gobject.IO_PRI | gobject.IO_OUT |
                               gobject.IO_ERR | gobject.IO_HUP)
        else:
            self.emit("error", IoError.CONNECTION_FAILED)
            self._status = IoStatus.CLOSED
        return False

    def _io_channel_handler(self, chan, cond):
        if self._status == IoStatus.CLOSED:
            return False
        if self._status == IoStatus.OPENING:
            try:
                self._transport.do_handshake()
            except (OpenSSL.WantX509LookupError,
                    OpenSSL.WantReadError, OpenSSL.WantWriteError):
                return True
            except (OpenSSL.ZeroReturnError, OpenSSL.SysCallError):
                self.emit("error", IoError.SSL_CONNECTION_FAILED)
                self.close()
                return False
            else:
                self._status = IoStatus.OPEN
        elif self._status == IoStatus.OPEN:
            if cond & (gobject.IO_IN | gobject.IO_PRI):
                try:
                    buf = ""
                    while True:
                        buf = self._transport.recv(2048)
                        self.emit("received", buf, len(buf))
                except (OpenSSL.WantX509LookupError,
                        OpenSSL.WantReadError, OpenSSL.WantWriteError):
                    return True
                except (OpenSSL.ZeroReturnError, OpenSSL.SysCallError):
                    self.close()
                    return False

            if cond & (gobject.IO_ERR | gobject.IO_HUP):
                self.close()
                return False

            if cond & gobject.IO_OUT:
                if len(self._outgoing_queue) > 0: # send next item
                    item = self._outgoing_queue[0]
                    try:
                        ret = self._transport.send(item.read())
                    except (OpenSSL.WantX509LookupError,
                            OpenSSL.WantReadError, OpenSSL.WantWriteError):
                        return True
                    except (OpenSSL.ZeroReturnError, OpenSSL.SysCallError):
                        self.close()
                        return False
                    item.sent(ret)
                    if item.is_complete(): # sent item
                        self.emit("sent", item.buffer, item.size)
                        item.callback()
                        del self._outgoing_queue[0]
                        del item
                    if len(self._outgoing_queue) == 0:
                        self._watch_remove_cond(gobject.IO_OUT)
                else:
                    self._watch_remove_cond(gobject.IO_OUT)

        return True

gobject.type_register(SSLSocketClient)
