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
import gzip
from papyon.gnet.constants import *
from papyon.gnet.errors import *
from papyon.util.odict import odict
import papyon.util.string_io as StringIO

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
            if line.strip() == "" or line == "\x00":
                if len(lines) >= i + 2:
                    self.body = "\r\n".join(lines[i+1:])
                break
            try:
                name, value = line.split(":", 1)
            except:
                raise HTTPParseError("Invalid header line: %s" % line)
            self.add_header(name.rstrip(), value.lstrip())

    def decode_body(self):
        """Decodes body content using "Content-Encoding" header. As of now
           only 'gzip' encoding is supported. Also encodes the result string
           to UTF-8 if necessary.
           @note Only 'gzip' encoding is supported for now
           @raises HTTPParseError: if encoding is unknown"""

        encoding = self.headers.get("Content-Encoding", "")
        if encoding == "":
            body = self.body
        elif encoding == "gzip":
            body_stream = StringIO.StringIO(self.body)
            unzipper = gzip.GzipFile(fileobj=body_stream)
            body = unzipper.read()
        else:
            raise HTTPParseError("%s is not implemented" % encoding)

        type, charset = self.content_type
        if charset.lower() != "utf-8":
            body = body.decode(charset).encode("utf-8")

        return body

    def __get_content_type(self):
        if 'Content-Type' in self.headers:
            content_type = self.headers['Content-Type'].split(';', 1)
            if len(content_type) == 1:
                return (content_type[0].strip(), 'UTF-8')
            mime_type = content_type[0].strip()
            encoding = content_type[1].split('=', 1)[1].strip()
            return (mime_type, encoding)
        return ('text/plain', 'UTF-8')
    
    def __set_content_type(self, content_type):
        if not isinstance(content_type, str):
            content_type = '; charset='.join(content_type)
        self.headers['Content-Type'] = content_type

    content_type = property(__get_content_type, __set_content_type,
            doc="a tuple specifying the content type")

    def __str__(self):
        result = []
        for name in self.headers.keys():
            result.append(": ".join((name, str(self.headers[name]))))
        #if "Content-Length" not in self.headers:
        #    result.append("Content-Length: %d" % len(body))
        result.append("")
        if "Content-Encoding" in self.headers:
            result.append("<" + self.headers.get('Content-Encoding', '') + " encoded data>")
        else:
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

