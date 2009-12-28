# -*- coding: utf-8 -*-
#
# Copyright (C) 2005  Ole André Vadla Ravnås <oleavr@gmail.com>
# Copyright (C) 2006  Ali Sabil <ali.sabil@gmail.com>
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

"""HTTP Messages structures."""
import cgi
from papyon.gnet.constants import *
from papyon.util.odict import odict

__all__ = ['HTTPMessage', 'HTTPResponse', 'HTTPRequest']

class HTTPMessage(object):
    """HTTP style message abstraction

        @ivar headers: HTTP style headers of the message
        @type headers: dict()

        @ivar body: HTTP Message Body
        @type body: string
    """
    def __init__(self):
        self.clear()
        
    def add_header(self, name, value):
        """Add the header with the given name to the set of headers of
        this message
            
            @param name: name of the header
            @param value: value of the header"""
        value = str(value)
        self.headers[name] = value

    def get_header(self, name):
        """Returns the value of a given header"""
        return self.headers[name]

    def clear(self):
        """Empties the HTTP message"""
        self.headers = odict()
        self.body = ""
        
    def parse(self, chunk):
        """Parses a given chunk of data and fill in the current object
        
            @param chunk: the chunk of data to parse
            @type chunk: string"""
        self.clear()

        lines = chunk.split("\r\n")
        for i, line in enumerate(lines):
            if line.strip() == "":
                self.body = "\r\n".join(lines[i+1:])
                break
            name, value = line.split(":", 1)
            self.add_header(name.rstrip(), value.lstrip())

    def __str__(self):
        result = []
        for name in self.headers.keys():
            result.append(": ".join((name, str(self.headers[name]))))
        #if "Content-Length" not in self.headers:
        #    result.append("Content-Length: %d" % len(body))
        result.append("")
        result.append(str(self.body))
        return "\r\n".join(result)

    def __unicode__(self):
        header = self.headers.get('Content-Type', '')
        charset = cgi.parse_header(header)[1].get('charset', 'iso8859-1')
        return str(self).decode(charset)


class HTTPResponse(HTTPMessage):
    def __init__(self, headers=None, body="", status=200, reason="OK", version="1.0"):
        if headers is None:
            headers = {}
        HTTPMessage.__init__(self)
        for header, value in headers.iteritems():
            self.add_header(header, value)
        self.body = body
        self.status = status
        self.reason = reason
        self.version = version

    def parse(self, chunk):
        start_line, message = chunk.split("\r\n", 1)
        
        version, status, reason  = start_line.split(" ", 2)
        self.status = int(status)
        self.reason = reason
        self.version = version.split("/",1)[1]

        HTTPMessage.parse(self, message)

    def __str__(self):
        message = HTTPMessage.__str__(self)
        start_line = "HTTP/%s %d %s" % (self.version, self.status, self.reason)
        return start_line + "\r\n" + message


class HTTPRequest(HTTPMessage):
    def __init__(self, headers=None, body="", method="GET", resource="/", version="1.0"):
        if headers is None:
            headers = {}
        HTTPMessage.__init__(self)
        for header, value in headers.iteritems():
            self.add_header(header, value)
        self.body = body
        self.method = method
        self.resource = resource
        self.version = version

    def parse(self, chunk):
        start_line, message = chunk.split("\r\n", 1)
        
        method, resource, version = start_line.split(" ")
        self.method = method
        self.resource = resource
        self.version = version.split("/",1)[1]

        HTTPMessage.parse(self, message)

    def __str__(self):
        message = HTTPMessage.__str__(self)
        start_line = "%s %s HTTP/%s" % (self.method,
                self.resource, self.version)
        return start_line + "\r\n" + message

