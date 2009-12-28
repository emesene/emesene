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
from papyon.gnet.resolver import *
from abstract import AbstractClient

import gobject
from errno import *

__all__ = ['GIOChannelClient']

class OutgoingPacket(object):
    """Represents a packet to be sent over the IO channel"""
    def __init__(self, buffer, size, callback=None, *cb_args):
        self.buffer = buffer
        self.size = size
        self._sent = 0
        self._callback = callback
        self._callback_args = cb_args

    def read(self, size=2048):
        if size is not None:
            return self.buffer[self._sent:][0:size]
        return self.buffer[self._sent:]

    def sent(self, size):
        """update how many bytes have been sent"""
        self._sent += size

    def is_complete(self):
        """return whether this packet was completely transmitted or not"""
        return self.size == self._sent

    def callback(self):
        """Run the callback function if supplied"""
        if self._callback is not None:
            self._callback(*self._callback_args)


class GIOChannelClient(AbstractClient):
    """Base class for clients using GIOChannel facilities

        @sort: __init__, open, send, close
        @undocumented: do_*, _configure, _pre_open, _post_open

        @since: 0.1"""

    def __init__(self, host, port, domain=AF_INET, type=SOCK_STREAM):
        AbstractClient.__init__(self, host, port, domain, type)

    def _pre_open(self, io_object):
        io_object.setblocking(False)
        channel = gobject.IOChannel(io_object.fileno())
        channel.set_flags(channel.get_flags() | gobject.IO_FLAG_NONBLOCK)
        channel.set_encoding(None)
        channel.set_buffered(False)

        self._transport = io_object
        self._channel = channel

        self._source_id = None
        self._source_condition = 0
        self._outgoing_queue = []
        AbstractClient._pre_open(self)

    def _post_open(self):
        AbstractClient._post_open(self)
        self._watch_remove()

    def _open(self, host, port):
        resolver = HostnameResolver()
        resolver.query(host, (self.__open, host, port))

    def __open(self, resolve_response, host, port):
        if resolve_response.status != 0:
            self.emit("error", IoError.CONNECTION_FAILED)
            self._transport.close()
            return
        else:
            host = resolve_response.answer[0][1]
        err = self._transport.connect_ex((host, port))
        self._watch_set_cond(gobject.IO_PRI | gobject.IO_IN | gobject.IO_OUT |
                gobject.IO_HUP | gobject.IO_ERR | gobject.IO_NVAL,
                lambda chan, cond: self._post_open())
        if err in (0, EINPROGRESS, EALREADY, EWOULDBLOCK, EISCONN):
            return
        elif err in (EHOSTUNREACH, EHOSTDOWN, ECONNREFUSED, ECONNABORTED,
                ENETUNREACH, ENETDOWN):
            self.emit("error", IoError.CONNECTION_FAILED)
            self._transport.close()

    # convenience methods
    def _watch_remove(self):
        if self._source_id is not None:
            gobject.source_remove(self._source_id)
            self._source_id = None
            self._source_condition = 0

    def _watch_set_cond(self, cond, handler=None):
        self._watch_remove()
        self._source_condition = cond
        if handler is None:
            handler = self._io_channel_handler
        self._source_id = self._channel.add_watch(cond, handler)

    def _watch_add_cond(self, cond):
        if self._source_condition & cond == cond:
            return
        self._source_condition |= cond
        self._watch_set_cond(self._source_condition)

    def _watch_remove_cond(self, cond):
        if self._source_condition & cond == 0:
            return
        self._source_condition ^= cond
        self._watch_set_cond(self._source_condition)

    # public API
    def open(self):
        if not self._configure():
            return
        self._pre_open()
        self._open(self._host, self._port)

    def close(self):
        if self._status in (IoStatus.CLOSING, IoStatus.CLOSED):
            return
        self._status = IoStatus.CLOSING
        self._watch_remove()
        try:
            self._channel.close()
            self._transport.shutdown(socket.SHUT_RDWR)
        except:
            pass
        self._transport.close()
        self._status = IoStatus.CLOSED

    def send(self, buffer, callback=None, *args):
        assert(self._status == IoStatus.OPEN), self._status
        self._outgoing_queue.append(OutgoingPacket(buffer, len(buffer),
            callback, *args))
        self._watch_add_cond(gobject.IO_OUT)
gobject.type_register(GIOChannelClient)
