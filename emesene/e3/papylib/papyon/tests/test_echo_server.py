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

import gobject
import logging
import socket
import struct
import sys
import time

sys.path.insert(0, "")

import papyon
from papyon.transport import DirectConnection, HTTPPollConnection
from papyon.gnet.constants import *
from papyon.gnet.io.tcp import TCPClient

class EchoClient(object):

    def __init__(self):
        self.transport = TCPClient("64.4.35.253", 7001)
        self.transport.connect("notify::status", self.on_status_changed)
        self.transport.connect("error", self.on_error)
        self.transport.connect("received", self.on_received)
        gobject.idle_add(self.open)

    def open(self):
        self.transport.open()

    def on_status_changed(self, transport, param):
        status = transport.get_property("status")
        print status
        if status == IoStatus.OPEN:
            print self.transport.sockname
            request = "\x02\x01\x41\x31\x41\x31\x41\x31\x00\x00\x00\x00\x00\x00\x00\x00\x5d\x00\x00\x00"
            self.transport.send(request)

    def on_error(self, transport, error):
        print "error", error

    def on_received(self, transport, data, lenght):
        fields = struct.unpack("!BBHIHHII", data)
        ver, code, port, ip, discard_port, test_port, test_ip, tr_id = fields
        port ^= 0x4131
        print repr(data)
        print ip
        ip ^= 0x41314131
        ip = socket.inet_ntoa(struct.pack("!I", ip))
        print ip, port

if __name__ == "__main__":

    logging.basicConfig(level=0)

    mainloop = gobject.MainLoop(is_running=True)
    client = EchoClient()
    mainloop.run()
