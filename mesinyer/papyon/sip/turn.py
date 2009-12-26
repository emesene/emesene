# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2009 Collabora Ltd.
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

from papyon.gnet.constants import *
from papyon.gnet.io.ssl_tcp import SSLTCPClient
from papyon.media.relay import MediaRelay
from papyon.service.SingleSignOn import *
from papyon.util.decorator import rw_property

import base64
import getpass
import gobject
import hashlib
import hmac
import random
import struct
import sys
import uuid

class MessageTypes(object):
    BINDING_REQUEST = 1
    SHARED_SECRET_REQUEST = 2
    ALLOCATE_REQUEST = 3
    BINDING_RESPONSE = 257
    SHARED_SECRET_RESPONSE = 258
    ALLOCATE_RESPONSE = 259
    BINDING_ERROR = 273
    SHARED_SECRET_ERROR = 274
    ALLOCATE_ERROR = 275

class AttributeTypes(object):
    MAPPED_ADDRESS = 1
    RESPONSE_ADDRESS = 2
    CHANGE_REQUEST = 3
    SOURCE_ADDRESS = 4
    CHANGED_ADDRESS = 5
    USERNAME = 6
    PASSWORD = 7
    MESSAGE_INTEGRITY = 8
    ERROR_CODE = 9
    UNKNOWN_ATTRIBUTES = 10
    REFLECTED_FROM = 11
    TRANSPORT_PREFERENCES = 12
    LIFETIME = 13
    ALTERNATE_SERVER = 14
    MAGIC_COOKIE = 15
    BANDWIDTH = 16
    MORE_AVAILABLE = 17
    REMOTE_ADDRESS = 18
    DATA = 19
    REALM = 20
    NONCE = 21
    RELAY_ADDRESS = 22
    REQUESTED_ADDRESS_TYPE = 23
    REQUESTED_PORT = 24
    REQUESTED_TRANSPORT = 25
    XOR_MAPPED_ADDRESS = 26
    TIMER_VAL = 27
    REQUESTED_IP = 28
    FINGERPRINT = 29
    SERVER = 32802
    ALTERNATE_SERVER = 32803
    REFRESH_INTERVAL = 32804

REQUEST_TIMEOUT = 5000 # milliseconds

class TURNClient(gobject.GObject):

    host = "relay.voice.messenger.msn.com"
    port = 443

    # Signal emitted when all requests were answered or failed
    __gsignals__ = {
        'done': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            (object,))
    }

    def __init__(self, sso, account):
        gobject.GObject.__init__(self)
        self._signals = []
        self._transport = SSLTCPClient(self.host, self.port)
        self._signals.append(self._transport.connect("notify::status",
            self.on_status_changed))
        self._signals.append(self._transport.connect("received",
            self.on_message_received))
        self._answered = False
        self._src = None
        self._msg_queue = []
        self._requests = {}
        self._relays = []
        self._account = account
        self._sso = sso
        self._tokens = {}

    def send(self, message):
        self._requests[message.id] = message
        if self._transport.status != IoStatus.OPEN:
            self._msg_queue.append(message)
            self._transport.open()
            return
        self._transport.send(str(message))

    @RequireSecurityTokens(LiveService.MESSENGER_SECURE)
    def request_shared_secret(self, callback, errcb, count=4):
        self._src = gobject.timeout_add(REQUEST_TIMEOUT, self.on_timeout)
        for _ in range(count):
            token = self._tokens[LiveService.MESSENGER_SECURE]
            username = "RPS_%s\x00\x00\x00" % token
            attrs = [TURNAttribute(AttributeTypes.USERNAME, username)]
            msg = TURNMessage(MessageTypes.SHARED_SECRET_REQUEST, attrs)
            self.send(msg)

    @RequireSecurityTokens(LiveService.MESSENGER_SECURE)
    def request_shared_secret_with_integrity(self, callback, errcb, realm, nonce):
        token = self._tokens[LiveService.MESSENGER_SECURE]
        username = "RPS_%s\x00\x00\x00" % token
        attrs = [TURNAttribute(AttributeTypes.USERNAME, username),
                 TURNAttribute(AttributeTypes.REALM, realm),
                 TURNAttribute(AttributeTypes.NONCE, nonce)]
        msg = TURNMessage(MessageTypes.SHARED_SECRET_REQUEST, attrs, 24)
        hmac = self.build_message_integrity(msg, token, nonce)
        msg.attributes.append(TURNAttribute(AttributeTypes.MESSAGE_INTEGRITY, hmac))
        msg.extra_size = 0
        self.send(msg)

    def build_message_integrity(self, msg, token, nonce):
        nonce = nonce.strip("\"")
        m = hashlib.md5()
        m.update("RPS_%s\x00\x00\x00:" % token)
        m.update("%s:%s" % (nonce, self._account))
        key = m.digest() + ("\x00" * 16)

        msg = str(msg)
        padding = 64 - (len(msg) % 64)
        if padding is 64:
            padding = 0
        msg += "\x00" * padding

        h = hmac.new(key, msg, hashlib.sha1)
        return h.digest()

    def on_status_changed(self, transport, param):
        if self._transport.status == IoStatus.OPEN:
            while self._msg_queue:
                self.send(self._msg_queue.pop())
        elif self._transport.status == IoStatus.CLOSED:
            self._done()

    def on_message_received(self, transport, data, length):
        msg = TURNMessage()
        msg.parse(data)

        if self._requests.get(msg.id, None) is None:
            return
        else:
            del self._requests[msg.id]

        if msg.type == MessageTypes.SHARED_SECRET_ERROR:
            error_msg = None
            realm = None
            nonce = None
            for attr in msg.attributes:
                if attr.type == AttributeTypes.REALM:
                    realm = attr.value
                elif attr.type == AttributeTypes.NONCE:
                    nonce = attr.value
                elif attr.type == AttributeTypes.ERROR_CODE:
                    error_msg = attr.value[4:]
            if error_msg == "Unauthorized":
                if realm is not None or nonce is not None:
                    self.request_shared_secret_with_integrity(None, None, realm, nonce)
                    return

        elif msg.type == MessageTypes.SHARED_SECRET_RESPONSE:
            relay = MediaRelay()
            for attr in msg.attributes:
                if attr.type == AttributeTypes.USERNAME:
                    relay.username = base64.b64encode(attr.value)
                elif attr.type == AttributeTypes.PASSWORD:
                    relay.password = base64.b64encode(attr.value)
                elif attr.type == AttributeTypes.ALTERNATE_SERVER:
                    server = struct.unpack("!HHcccc", attr.value)
                    ip = map(lambda x: ord(x), server[2:6])
                    relay.ip = "%i.%i.%i.%i" % tuple(ip)
                    relay.port = server[1]
            self._relays.append(relay)

        if not self._requests:
            self._done()

    def on_timeout(self):
        self._done()
        return False

    def _done(self):
        if not self._answered:
            self._answered = True
            self._requests = {}
            self._msg_queue = []
            for signal_id in self._signals:
                self._transport.disconnect(signal_id)
            if self._src is not None:
                gobject.source_remove(self._src)
                self._src = None
            self.emit("done", self._relays)
        self._transport.close()


class TURNMessage(object):

    def __init__(self, type=None, attributes=[], extra_size=0):
        self.type = type
        self._attributes = attributes
        self._extra_size = extra_size
        self._id = int(uuid.uuid4())

    @property
    def id(self):
        return self._id

    @property
    def attributes(self):
        return self._attributes

    @rw_property
    def extra_size():
        def fget(self):
            return self._extra_size
        def fset(self, value):
            self._extra_size = value
        return locals()

    def split_id(self):
        parts = []
        id = self._id
        for i in range(0, 4):
            parts.append(int(id & 0xFFFFFFFF))
            id >>= 32
        parts.reverse()
        return parts

    def merge_id(self, parts):
        self._id = 0
        for part in parts:
            self._id += part
            self._id <<= 32
        self._id >>= 32

    def parse(self, msg):
        hdr = struct.unpack("!HH4I", msg[0:20])
        self.type = hdr[0]
        self.merge_id(hdr[2:])

        msg = msg[20:]
        while msg:
            attr = TURNAttribute()
            attr.parse(msg)
            self._attributes.append(attr)
            msg = msg[len(attr):]

    def __str__(self):
        msg = ""
        for attr in self._attributes:
            msg += str(attr)
        id = self.split_id()
        hdr = struct.pack("!HH4I", self.type, len(msg) + self._extra_size,
                          id[0], id[1], id[2], id[3])
        return (hdr + msg)


class TURNAttribute(object):

    def __init__(self, type=None, value=None):
        self.type = type
        self._value = value

    @property
    def value(self):
        return self._value

    def parse(self, msg):
        type, size = struct.unpack("!HH", msg[0:4])
        self.type = type
        self._value = msg[4:size+4]

    def __len__(self):
        return len(self._value) + 4

    def __str__(self):
        attr = struct.pack("!HH", self.type, len(self._value))
        attr += self._value
        return attr


if __name__ == "__main__":

    if len(sys.argv) < 2:
        account = raw_input('Account: ')
    else:
        account = sys.argv[1]

    if len(sys.argv) < 3:
        password = getpass.getpass('Password: ')
    else:
        password = sys.argv[2]

    mainloop = gobject.MainLoop(is_running=True)
    sso = SingleSignOn(account, password)
    client = TURNClient(sso, account)
    client.request_shared_secret(None, None, 2)
    mainloop.run()
