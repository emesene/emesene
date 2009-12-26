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

from papyon.sip.constants import *
from papyon.util.decorator import rw_property

import gobject
import logging

__all__ = ['SIPMessage', 'SIPRequest', 'SIPResponse', 'SIPMessageParser']

logger = logging.getLogger('papyon.sip.parser')


class SIPMessage(object):
    """Represent a SIP message. Both Requests and Responses follow basic
       format of RFC 2822 (except the set of valid headers is different).
       Also, the majority of possible headers has a long and a compact form."""

    def __init__(self):
        self._body = None
        self._call = None
        self._headers = {}
        self.set_content("")
        self.sent = False
        self.cancelled = False

    @rw_property
    def body():
        def fget(self):
            return self._body
        def fset(self, value):
            self._body = value
        return locals()

    @rw_property
    def call():
        def fget(self):
            return self._call
        def fset(self, value):
            self._call = value
        return locals()

    @property
    def length(self):
        return int(self.get_header("Content-Length", 0))

    def normalize_name(self, name):
        name = name.lower()
        if len(name) is 1:
            for long, compact in COMPACT_HEADERS.iteritems():
                if name == compact:
                    return long
        return name

    def add_header(self, name, value):
        name = self.normalize_name(name)
        if name in UNIQUE_HEADERS:
            self._headers[name] = [value]
        else:
            self._headers.setdefault(name, []).append(value)

    def set_header(self, name, value):
        name = self.normalize_name(name)
        self._headers[name] = [value]

    def get_headers(self, name, default=None):
        name = self.normalize_name(name)
        return self._headers.get(name, default)

    def get_header(self, name, default=None):
        value = self.get_headers(name, default)
        if type(value) == list:
            return value[0]
        return value

    def clone_headers(self, name, other, othername=None):
        if othername is None:
            othername = name
        name = self.normalize_name(name)
        othername = self.normalize_name(othername)
        values = other.get_headers(othername)
        if values is not None:
            self._headers[name] = values

    def set_content(self, content, type=None):
        if type:
            self.set_header("Content-Type", type)
        self.set_header("Content-Length", len(content))
        self._body = content

    def get_header_line(self):
        raise NotImplementedError

    def __str__(self):
        s = [self.get_header_line()]
        for k, v in self._headers.items():
            for value in v:
                s.append("%s: %s" % (k, value))
        s.append("")
        s.append(self._body)
        return "\r\n".join(s)


class SIPRequest(SIPMessage):

    def __init__(self, code, uri):
        SIPMessage.__init__(self)
        self._code = code
        self._uri = uri

    @property
    def code(self):
        return self._code

    @property
    def uri(self):
        return self._uri

    def get_header_line(self):
        return "%s %s SIP/2.0" % (self._code, self._uri)

    def __repr__(self):
        return "<SIP Request %d:%s %s>" % (id(self), self._code, self._uri)


class SIPResponse(SIPMessage):

    def __init__(self, status, reason=None):
        SIPMessage.__init__(self)
        self._status = status
        if not reason:
            reason = RESPONSE_CODES[status]
        self._reason = reason

    @property
    def code(self):
        cseq = self.get_header("CSeq")
        if not cseq:
            return None
        return cseq.split()[1]

    @property
    def status(self):
        return self._status

    @property
    def reason(self):
        return self._reason

    def get_header_line(self):
        return "SIP/2.0 %s %s" % (self._status, self._reason)

    def __repr__(self):
        return "<SIP Response %d:%s %s>" % (id(self), self._status, self._reason)


class SIPMessageParser(gobject.GObject):

    version = "SIP/2.0"

    __gsignals__ = {
        'message-parsed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            ([object]))
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        self.reset()

    def reset(self):
        self._message = None
        self._length = 0
        self._state = "start"
        self._buffer = ""

    def append(self, chunk):
        self._buffer += chunk
        finished = False
        try:
            while not finished:
                finished = self.parse_buffer()
        except Exception, err:
            logger.error("Error while parsing received message: %s", err)
            self.reset()

    def parse_buffer(self):
        if self._state == "start":
            line = self.consume_line()
            if line is None:
                return True
            a, b, c = line.split(" ", 2)
            if a == self.version:
                code = int(b)
                self._message = SIPResponse(code, c)
            elif c == self.version:
                self._message = SIPRequest(a, b)
            self._state = "headers"

        if self._state == "headers":
            line = self.consume_line()
            if line is None:
                return True
            elif line == "":
                self._state = "body"
            else:
                name, value = line.split(":", 1)
                self._message.add_header(name, value.strip())

        if self._state == "body":
            missing = self._message.length - len(self._message.body)
            self._message.body += self.consume_chars(missing)
            if len(self._message.body) >= self._message.length:
                self._state = "done"
            else:
                return True

        if self._state == "done":
            self.emit("message-parsed", self._message)
            self.reset()
            return True

        return False

    def consume_line(self):
        try:
            line, self._buffer = self._buffer.split("\r\n", 1)
        except:
            # Incomplete line: all lines have to end with '\r\n'
            # Don't return anything, maybe the rest of the line would arrive in
            # another packet
            return None
        return line

    def consume_chars(self, count):
        if count is 0:
            ret = ""
        elif count >= len(self._buffer):
            ret = self._buffer
            self._buffer = ""
        else:
            ret = self._buffer[0:count]
            self._buffer = self._buffer[count:]
        return ret
