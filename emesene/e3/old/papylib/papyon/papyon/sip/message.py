# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2009-2010 Collabora Ltd.
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

from papyon.errors import ParseError
from papyon.sip.constants import *
from papyon.util.decorator import rw_property

import gobject
import logging
import re
import weakref

__all__ = ['SIPMessage', 'SIPRequest', 'SIPResponse', 'SIPParseError',
           'SIPMessageParser']

logger = logging.getLogger('papyon.sip.parser')


class SIPParseError(ParseError):
    """SIP Parsing Error"""
    def __init__(self, message, infos=''):
        ParseError.__init__(self, "SIP", message, infos)


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

    @property
    def required_extensions(self):
        return set(self.get_header("Require", "").split())

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

    def parse_header(self, name, value):
        name = self.normalize_name(name)
        try:
            if name in ("contact", "from", "to"):
                value = SIPContact.build(value)
            elif name == "cseq":
                value = SIPCSeq.build(value)
            elif name in ("record-route", "route"):
                value = SIPRoute.build(value)
            elif name == "via":
                value = SIPVia.build(value)
        except:
            raise SIPParseError("invalid %s header value: %s" % (name, value))
        self.add_header(name, value)

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

    def match_header(self, name, other):
        value = self.get_header(name)
        other_value = other.get_header(name)
        return value == other_value

    def match_headers(self, names, other):
        for name in names:
            if not self.match_header(name, other):
                return False
        return True

    def clone_headers(self, name, other, othername=None):
        if othername is None:
            othername = name
        name = self.normalize_name(name)
        othername = self.normalize_name(othername)
        values = other.get_headers(othername)
        if values is not None:
            cloned_values = []
            for value in values:
                if hasattr(value, "clone"):
                    cloned_value = value.clone()
                else:
                    cloned_value = value
                cloned_values.append(cloned_value)
            self._headers[name] = cloned_values

    def set_content(self, content):
        if hasattr(content, "type"):
            self.set_header("Content-Type", content.type)
        body = str(content)
        self.set_header("Content-Length", len(body))
        self._body = body

    def get_header_line(self):
        raise NotImplementedError

    def __getattr__(self, name):
        name = name.replace('_', '-')
        return self.get_header(name)

    def __str__(self):
        s = [self.get_header_line()]
        for k, v in self._headers.items():
            for value in v:
                s.append("%s: %s" % (k, str(value)))
        s.append("")
        s.append(self._body)
        return "\r\n".join(s)


class SIPRequest(SIPMessage):

    def __init__(self, code, uri):
        SIPMessage.__init__(self)
        self.code = code
        self.uri = uri
        self._transaction_ref = None

    @rw_property
    def transaction():
        def fget(self):
            if self._transaction_ref is None:
                return None
            return self._transaction_ref()
        def fset(self, value):
            if value is None:
                self._transaction_ref = None
            else:
                self._transaction_ref = weakref.ref(value)
        return locals()

    def get_header_line(self):
        return "%s %s SIP/2.0" % (self.code, self.uri)

    def __repr__(self):
        return "<SIP Request %d:%s %s>" % (id(self), self.code, self.uri)


class SIPResponse(SIPMessage):

    def __init__(self, status, reason=None):
        SIPMessage.__init__(self)
        self._request_ref = None
        self._status = status
        if not reason and status in RESPONSE_CODES:
            reason = RESPONSE_CODES[status]
        self._reason = reason

    @rw_property
    def request():
        def fget(self):
            if self._request_ref is None:
                return None
            return self._request_ref()
        def fset(self, value):
            if value is None:
                self._request_ref = None
            else:
                self._request_ref = weakref.ref(value)
        return locals()

    @property
    def code(self):
        return self.cseq.method

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
            logger.exception(err)
            logger.error("Error while parsing received message")
            self.reset()

    def parse_buffer(self):
        if self._state == "start":
            line = self.consume_line()
            if line is None:
                return True
            try:
                a, b, c = line.split(" ", 2)
                if a == self.version:
                    code = int(b)
                    self._message = SIPResponse(code, c)
                elif c == self.version:
                    self._message = SIPRequest(a, b)
                else:
                    raise ValueError
            except ValueError:
                raise SIPParseError("invalid start line", line)
            self._state = "headers"

        if self._state == "headers":
            line = self.consume_line()
            if line is None:
                return True
            elif line == "":
                self._state = "body"
            else:
                if not ':' in line:
                    raise SIPParseError("invalid header line (no colon)", line)
                name, value = line.split(":", 1)
                self._message.parse_header(name, value.strip())

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


### SIP Message Headers

class SIPContact(object):
    def __init__(self, name, uri, tag=None, params=None):
        self.name = name
        self.uri = uri
        self.tag = tag
        if params is None:
            params = {}
        self.params = params

    @staticmethod
    def build(line):
        contact_spec = "(\"(?P<name>[^\"]*)\")? *\<(?P<uri>[^>]*)\>(;tag=(?P<tag>[^;>]*))?(?P<params>;[^;>]*)*"
        m = re.match(contact_spec, line)
        if not m:
            return None
        params = {}
        if m.group("params"):
            for param in m.group("params").split(";"):
                if "=" in param:
                    key, value = param.split("=")
                    params[key] = value
        return SIPContact(m.group("name"), m.group("uri"), m.group("tag"), params)

    def clone(self):
        params = self.params.copy()
        return SIPContact(self.name, self.uri, self.tag, params)

    def __str__(self):
        line = ""
        if self.name:
            line += "\"%s\" " % self.name
        line += "<%s>" % str(self.uri)
        if self.tag:
            line += ";tag=%s" % self.tag
        for key,value in self.params.items():
            line += ";%s=%s" % (key, str(value))
        return line

    def __eq__(self, other):
        return (self.uri == other.uri and
                self.tag == other.tag and
                self.params == other.params)

class SIPCSeq(object):
    def __init__(self, number, method):
        self.number = number
        self.method = method

    @staticmethod
    def build(line):
        number, method = line.split(" ", 2)
        return SIPCSeq(int(number), method)

    def clone(self):
        return SIPCSeq(self.number, self.method)

    def __str__(self):
        return "%i %s" % (self.number, self.method)

    def __eq__(self, other):
        return (self.number == other.number and self.method == other.method)

class SIPRoute(object):
    def __init__(self, route_set):
        self.route_set = route_set

    @staticmethod
    def build(line):
        items = line.split(",")
        route_set = map(lambda item: re.search("<([^>]*)>", item).group(1), items)
        return SIPRoute(route_set)

    def clone(self):
        return SIPRoute(self.route_set[:])

    def __str__(self):
        return ",".join(map(lambda item: "<%s>" % item, self.route_set))

    def __eq__(self, other):
        return (self.route_set == other.route_set)

class SIPVia(object):
    def __init__(self, protocol=None, ip=None, port=None, branch=None):
        self.protocol = protocol.upper()
        self.ip = ip
        self.port = port
        self.branch = branch

    @staticmethod
    def build(line):
        via_spec = "SIP/2.0/(?P<protocol>[a-zA-Z]*) (?P<ip>[0-9\.]*):(?P<port>[0-9]*)(;branch=(?P<branch>[^;>]*))?"
        m = re.match(via_spec, line)
        if not m:
            return None
        return SIPVia(m.group("protocol"), m.group("ip"),
                int(m.group("port")), m.group("branch"))

    def clone(self):
        return SIPVia(self.protocol, self.ip, self.port, self.branch)

    def __str__(self):
        line = "SIP/2.0/%s %s:%d" % (self.protocol, self.ip, self.port)
        if self.branch:
            line += ";branch=%s" % self.branch
        return line

    def __eq__(self, other):
        return (self.protocol == other.protocol and
                self.ip == other.ip and self.port == self.port and
                self.branch == other.branch)
