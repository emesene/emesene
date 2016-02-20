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

from papyon.errors import ClientError, ClientErrorType, ParseError
from papyon.gnet.constants import *
from papyon.gnet.io.ssl_tcp import SSLTCPClient
from papyon.media.relay import MediaRelay
from papyon.service.SingleSignOn import *
from papyon.util.async import run
from papyon.util.debug import hexify_string
from papyon.util.decorator import rw_property
from papyon.util.timer import Timer

import base64
import getpass
import gobject
import hashlib
import hmac
import logging
import random
import socket
import struct
import sys
import uuid

logger = logging.getLogger('papyon.turn')

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
    #ALTERNATE_SERVER = 32803
    REFRESH_INTERVAL = 32804

class TURNErrorCode(object):
   BAD_REQUEST = 400
   UNAUTHORIZED = 401
   UNKNOWN_ATTRIBUTE = 420
   STALE_CREDENTIALS = 430
   INTEGRITY_CHECK_FAILURE = 431
   MISSING_USERNAME = 432
   USE_TLS = 433
   SERVER_ERROR = 500
   GLOBAL_FAILURE = 600

REQUEST_TIMEOUT = 5 # seconds


class TURNError(ClientError):
    """TURN Error"""
    def __init__(self, code, reason=''):
        ClientError.__init__(self, ClientErrorType.UNKNOWN, code)
        self.reason = reason

    def __str__(self):
        return "TURN Error (%i): %s" % (self._code, self.reason)

class TURNParseError(ParseError):
    """TURN Parsing Error"""
    def __init__(self, message, infos=''):
        ParseError.__init__(self, "TURN", message, infos)


class TURNClient(gobject.GObject, Timer):

    def __init__(self, sso, account, host="relay.voice.messenger.msn.com", port=443):
        gobject.GObject.__init__(self)
        Timer.__init__(self)

        self._sso = sso
        self._account = account

        self._signals = []
        self._transport = SSLTCPClient(host, port)
        self._signals.append(self._transport.connect("notify::status",
            self.on_status_changed))
        self._signals.append(self._transport.connect("received",
            self.on_message_received))

        self._tokens = {}
        self._msg_queue = []
        self._transactions = {}  # id => (initial_request)
        self._request_id = 0
        self._requests = {} # id => (callback, errback, count, relays)

    def send(self, message):
        self._transactions[message.id] = message
        if self._transport.status != IoStatus.OPEN:
            self._msg_queue.append(message)
            self._transport.open()
            return
        self._transport.send(str(message))

    @RequireSecurityTokens(LiveService.MESSENGER_SECURE)
    def request_shared_secret(self, callback, errback, count=1):
        logger.info("Sending shared secret requests (%i)" % count)

        self._request_id += 1
        self._requests[self._request_id] = (callback, errback, count, [])
        self.start_timeout_with_id("request", self._request_id, REQUEST_TIMEOUT)

        for _ in range(count):
            token = self._tokens[LiveService.MESSENGER_SECURE]
            username = "RPS_%s\x00\x00\x00" % token
            attrs = [TURNAttribute(AttributeTypes.USERNAME, username)]
            msg = TURNMessage(None, MessageTypes.SHARED_SECRET_REQUEST, attrs)
            self.send(msg)

    @RequireSecurityTokens(LiveService.MESSENGER_SECURE)
    def request_shared_secret_with_integrity(self, callback, errcb, realm, nonce):
        logger.info("Sending shared secret request with integrity")

        token = self._tokens[LiveService.MESSENGER_SECURE]
        username = "RPS_%s\x00\x00\x00" % token
        attrs = [TURNAttribute(AttributeTypes.USERNAME, username),
                 TURNAttribute(AttributeTypes.REALM, realm),
                 TURNAttribute(AttributeTypes.NONCE, nonce)]
        msg = TURNMessage(None, MessageTypes.SHARED_SECRET_REQUEST, attrs, 24)
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
            pass #TODO something..

    def on_message_received(self, transport, data, length):
        try:
            msg = parse_message(data)

            initial_request = self._transactions.pop(msg.id, None)
            if initial_request is None:
                logger.warning("Received TURN response with invalid ID")
                return

            if msg.type == MessageTypes.SHARED_SECRET_ERROR:
                self.on_shared_secret_error(msg)
            elif msg.type == MessageTypes.SHARED_SECRET_RESPONSE:
                self.on_shared_secret_response(msg)
            else:
                logger.warning("Received unexpected message: %i" % msg.type)

        except Exception, e:
            logger.exception(e)
            logger.error("Received invalid TURN message")

    def on_shared_secret_error(self, msg):
        logger.info("Received shared secret error")
        error = None
        realm = None
        nonce = None
        for attr in msg.attributes:
            if attr.type == AttributeTypes.REALM:
                realm = attr.value
            elif attr.type == AttributeTypes.NONCE:
                nonce = attr.value
            elif attr.type == AttributeTypes.ERROR_CODE:
                error = parse_error(attr.value)
        if error == TURNErrorCode.UNAUTHORIZED:
            if realm is not None or nonce is not None:
                self.request_shared_secret_with_integrity(None, None,
                        realm, nonce)
            else:
                raise TURNParseError("missing REALM or NONCE attribute")
        elif error is None:
            raise TURNParseError("missing ERROR-CODE attribute")
        else:
            raise error

    def on_shared_secret_response(self, msg):
        logger.info("Received shared secret response")
        relay = MediaRelay()
        for attr in msg.attributes:
            if attr.type == AttributeTypes.USERNAME:
                relay.username = base64.b64encode(attr.value)
            elif attr.type == AttributeTypes.PASSWORD:
                relay.password = base64.b64encode(attr.value)
            elif attr.type == AttributeTypes.ALTERNATE_SERVER:
                relay.ip, relay.port = parse_server(attr.value)
        self.on_relay_discovered(relay)

    def on_relay_discovered(self, relay):
        logger.info("Discovered %s" % str(relay))
        keys = self._requests.keys()
        if not keys:
            logger.warning("No active request necessitating new relay")
            return
        keys.sort()
        callback, errback, count, result = self._requests.get(keys[0])
        result.append(relay)
        if len(result) >= count:
            del self._requests[keys[0]]
            run(callback, result)
        if not self._requests:
            self.stop_all_timeout()
            self._transport.close()

    def on_request_timeout(self, id):
        if id not in self._requests:
            return
        logger.info("Timeout on TURN request")
        callback, errback, count, result = self._requests.pop(id)
        run(callback, result)
        if not self._requests:
            self._transport.close()


class TURNMessage(object):

    def __init__(self, id, type, attributes=[], extra_size=0):
        if id is None:
            id = uuid.uuid4()

        self._id = id
        self._type = type
        self._attributes = attributes
        self._extra_size = extra_size

    @property
    def id(self):
        return self._id

    @property
    def type(self):
        return self._type

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

    def __str__(self):
        msg = ""
        for attr in self._attributes:
            msg += str(attr)
        size = len(msg) + self._extra_size
        hdr = struct.pack("!HH16s", self._type, size, self._id.bytes)
        return (hdr + msg)


class TURNAttribute(object):

    def __init__(self, type, value):
        self._type = type
        self._value = value

    @property
    def type(self):
        return self._type

    @property
    def value(self):
        return self._value

    def __len__(self):
        return len(self._value) + 4

    def __str__(self):
        attr = struct.pack("!HH", self._type, len(self._value))
        attr += self._value
        return attr


### Helper functions ---------------------------------------------------------

def parse_message(msg):
    if len(msg) < 20:
        raise TURNParseError("message must be a least 20 bytes long",
                hexify_string(msg))

    try:
        hdr = struct.unpack("!HH16s", msg[:20])
    except:
        raise TURNParseError("invalid message header", hexify_string(msg[:20]))

    type = hdr[0]
    id = uuid.UUID(bytes=hdr[2])
    attributes = []
    msg = msg[20:]
    while msg:
        attr = parse_attribute(msg)
        attributes.append(attr)
        msg = msg[len(attr):]
    return TURNMessage(id, type, attributes)

def parse_attribute(msg):
    if len(msg) < 4:
        raise TURNParseError("attribute must be at least 4 bytes long",
                hexify_string(msg))
    try:
        type, size = struct.unpack("!HH", msg[:4])
    except:
        raise TURNParseError("invalid attribute", hexify_string(msg[:4]))

    value = msg[4:size+4]
    return TURNAttribute(type, value)

def parse_error(value):
    try:
        values = struct.unpack("!HBB", value[0:4])
    except:
        raise TURNParseError("invalid error attribute", hexify_string(value))

    code = values[1] * 100 + values[2]
    reason = value[4:]
    return TURNError(code, reason)

def parse_server(value):
    try:
        server = struct.unpack("!HH4s", value)
    except:
        raise TURNParseError("invalid server attribute", hexify_string(value))

    ip = socket.inet_ntoa(server[2])
    port = server[1]
    if port == 0:
        port = 1863
    return ip, port


if __name__ == "__main__":

    if len(sys.argv) < 2:
        account = raw_input('Account: ')
    else:
        account = sys.argv[1]

    if len(sys.argv) < 3:
        password = getpass.getpass('Password: ')
    else:
        password = sys.argv[2]

    logging.basicConfig(level=0)
    mainloop = gobject.MainLoop(is_running=True)
    sso = SingleSignOn(account, password)
    client = TURNClient(sso, account)
    client.request_shared_secret(None, None, 2)
    mainloop.run()
